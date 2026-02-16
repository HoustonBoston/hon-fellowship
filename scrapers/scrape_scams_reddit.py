#!/usr/bin/env python3
"""
Reddit Subreddit Scraper
========================
Scrapes all posts and nested comments from a subreddit using Selenium
(to render JavaScript-loaded content) and BeautifulSoup (to parse HTML).

Reddit's modern interface loads content dynamically, so we use Selenium
to scroll through pages and expand comment trees, then parse the fully
rendered HTML with BeautifulSoup.

Usage:
    python scrape_scams_reddit.py
    python scrape_scams_reddit.py --subreddit cryptocurrency --max-posts 50
"""

import argparse
import json
import os
import time
import random
from datetime import datetime
import undetected_chromedriver as uc
from selenium_stealth import stealth

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Use old.reddit.com — its HTML structure is simpler and more stable for
# scraping than the new React-based UI.
BASE_URL = "https://old.reddit.com"
DEFAULT_SUBREDDIT = "Scams"

# How many seconds to wait for elements to appear before giving up.
WAIT_TIMEOUT = 10

# Pause between requests so we stay under 100 requests / minute.
# 60s ÷ 100 = 0.6s minimum gap; we use 0.65s for a small safety margin.
POLITE_DELAY = 1

# Rate-limit (HTTP 429) cooldown settings.
# When Reddit returns a 429, we wait COOLDOWN_BASE seconds and then
# double the wait on each consecutive 429, up to COOLDOWN_MAX seconds.
COOLDOWN_BASE = 30      # initial cooldown in seconds
COOLDOWN_MAX = 300      # maximum cooldown (5 minutes)
MAX_RETRIES = 50          # give up after this many consecutive 429s


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

def create_driver() -> uc.Chrome:
    """
    Create and return a headless Chrome WebDriver instance.

    We run headless so this can work on servers without a display.
    A custom User-Agent is set so Reddit doesn't serve a stripped-down
    page intended for bots.
    """
    options = uc.ChromeOptions()
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument('--incognito')

    driver = uc.Chrome(headless=False, use_subprocess=True, options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32"
    )
    return driver


def _is_rate_limited(driver: uc.Chrome) -> bool:
    """
    Check whether the current page is a Reddit 429 rate-limit response.

    Since we're using Selenium (not raw HTTP), there's no status code to
    inspect directly.  Instead we look for telltale signs in the page
    source: the literal string "429" in the title, or Reddit's
    "you are doing that too much" / "too many requests" messaging.
    """
    # Checking page_source is cheap — no extra network request.
    src = driver.page_source.lower()
    indicators = [
        "this page isn't working",
        "https_error"
    ]
    return any(ind in src for ind in indicators)


def safe_get(driver: uc.Chrome, url: str) -> None:
    """
    Navigate to *url* with automatic retry + exponential back-off when
    Reddit returns an HTTP 429 (rate-limit) page.

    After each failed attempt the function sleeps for an exponentially
    increasing duration (COOLDOWN_BASE, 2x, 4x, … capped at
    COOLDOWN_MAX) before retrying.  Raises RuntimeError after
    MAX_RETRIES consecutive failures.
    """

    print("safely getting")

    sleep_random()

    cooldown = COOLDOWN_BASE

    for attempt in range(1, MAX_RETRIES + 1):
        driver.get(url)
        # return  # temporarily
        # sleep_random()

        if not _is_rate_limited(driver):
            return  # success — page loaded normally

        # We hit a 429.  Log it and back off.
        print(
            f"  [429] Rate-limited on attempt {attempt}/{MAX_RETRIES}. "
            f"Cooling down for {cooldown}s …"
        )
        time.sleep(cooldown)
        cooldown = min(cooldown * 2, COOLDOWN_MAX)  # exponential back-off

    # If we exhausted all retries, raise so the caller can decide what to do.
    raise RuntimeError(
        f"Still rate-limited after {MAX_RETRIES} retries for URL: {url}"
    )

def sleep_random():
    sleep_t = random.triangular(1, 4, 3)
    print(f"sleeping for {sleep_t:.2f} seconds …")
    time.sleep(sleep_t)    # be polite and avoid hammering the server


# ---------------------------------------------------------------------------
# Subreddit listing scraper  (grabs post URLs)
# ---------------------------------------------------------------------------

def scrape_post_urls(driver: uc.Chrome, subreddit: str,
                    max_posts: int = 10000) -> list[str]:
    """
    Scroll through the subreddit listing on old.reddit.com and collect
    post URLs until we reach *max_posts* or run out of pages.

    old.reddit.com paginates with a "next" button rather than infinite
    scroll, which makes it straightforward to iterate over all pages.

    Returns a list of full URLs to individual post pages.
    """
    collected_urls: list[str] = []
    # Start on the first page of the subreddit (sorted by "new" to get
    # chronological order, but you could use /hot/ or /top/ instead).
    page_url = f"{BASE_URL}/r/{subreddit}/new/"

    while page_url and len(collected_urls) < max_posts:
        print(f"[listing] Loading page: {page_url}")
        safe_get(driver, page_url)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Each post on old.reddit.com lives inside a <div class="thing">.
        # The permalink is in a child <a> with data-event-action="comments".
        for thing in soup.select("div.thing"):
            # Skip stickied / promoted posts
            if "stickied" in thing.get("class", []) or "promoted" in thing.get("class", []):
                continue

            link_tag = thing.select_one("a.comments")
            if link_tag and link_tag.get("href"):
                full_url = link_tag["href"]
                # old.reddit.com already gives absolute URLs here
                if not full_url.startswith("http"):
                    full_url = BASE_URL + full_url
                collected_urls.append(full_url)

            if len(collected_urls) >= max_posts:
                break

        # Find the "next" page button to continue pagination.
        next_btn = soup.select_one("span.next-button a")
        page_url = next_btn["href"] if next_btn else None

    print(f"[listing] Collected {len(collected_urls)} post URLs.")
    return collected_urls


# ---------------------------------------------------------------------------
# Comment parser  (recursive, handles arbitrary nesting)
# ---------------------------------------------------------------------------

def parse_comment(comment_div, depth: int = 0) -> dict | None:
    """
    Recursively parse a single comment <div> from old.reddit.com and all
    of its nested child replies.

    Parameters
    ----------
    comment_div : bs4.element.Tag
        A <div> with class "comment" from old.reddit.com's HTML.
    depth : int
        Current nesting level (0 = top-level comment).

    Returns
    -------
    dict or None
        A dictionary with the comment data and a ``replies`` list that
        may itself contain nested comment dicts.  Returns None if the
        comment is deleted/removed and has no useful content.
    """
    # --- Extract the author ------------------------------------------------
    author_tag = comment_div.select_one("a.author")
    author = author_tag.get_text(strip=True) if author_tag else "[deleted]"

    # --- Extract the comment body ------------------------------------------
    body_tag = comment_div.select_one("div.md")
    body = body_tag.get_text(separator="\n", strip=True) if body_tag else ""

    # --- Extract the score (upvotes) ---------------------------------------
    score_tag = comment_div.select_one("span.score.unvoted")
    score_text = score_tag.get_text(strip=True) if score_tag else "0 points"

    # --- Extract the timestamp ---------------------------------------------
    time_tag = comment_div.select_one("time")
    timestamp = time_tag.get("datetime", "") if time_tag else ""

    # --- Extract the comment permalink / id --------------------------------
    permalink_tag = comment_div.select_one("a.bylink")
    permalink = permalink_tag["href"] if permalink_tag else ""

    # Skip completely empty / deleted comments with no replies
    if not body and author == "[deleted]":
        # Still parse children — sometimes a deleted parent has live replies
        pass

    # --- Recursively parse child (nested) replies --------------------------
    # On old.reddit.com, replies live inside a <div class="child"> that
    # contains its own list of <div class="comment"> elements.
    replies: list[dict] = []
    child_area = comment_div.select_one("div.child")
    if child_area:
        # Direct children only (recursive=False) to avoid double-counting
        # deeper levels — each level calls parse_comment on its own children.
        for child_comment in child_area.find_all(
            "div", class_="comment", recursive=False
        ):
            parsed = parse_comment(child_comment, depth=depth + 1)
            if parsed:
                replies.append(parsed)

    return {
        "author": author,
        "body": body,
        "score": score_text,
        "timestamp": timestamp,
        "permalink": permalink,
        "depth": depth,
        "replies": replies,
    }


# ---------------------------------------------------------------------------
# Single-post scraper  (post metadata + full comment tree)
# ---------------------------------------------------------------------------

def expand_hidden_comments(driver: uc.Chrome) -> None:
    """
    Click all "load more comments" and "[+] expand" links on the page so
    that Selenium renders the complete comment tree before we hand the
    HTML off to BeautifulSoup.

    This loops until no new expandable links are found.
    """
    while True:
        try:
            # old.reddit.com uses <a class="morecomments"> for "load more
            # comments" links and <a class="expand"> for collapsed threads.
            more_links = driver.find_elements(
                By.CSS_SELECTOR, "a.morecomments, span.morecomments a"
            )
            if not more_links:
                break

            clicked_any = False
            for link in more_links:
                try:
                    driver.execute_script("arguments[0].click();", link)
                    clicked_any = True
                    sleep_random()
                except (StaleElementReferenceException,
                        ElementClickInterceptedException):
                    # Element may have been replaced by newly loaded HTML.
                    continue

            if not clicked_any:
                break

        except Exception:
            break


def scrape_post(driver: uc.Chrome, post_url: str) -> dict:
    """
    Navigate to a single Reddit post, expand all comments, and return a
    structured dictionary containing the post metadata and the full
    nested comment tree.

    Parameters
    ----------
    driver : uc.Chrome
        An active Selenium WebDriver session.
    post_url : str
        The full URL of the Reddit post to scrape.

    Returns
    -------
    dict
        Keys: title, author, score, url, selftext, timestamp,
              num_comments, comments (list of nested dicts).
    """
    print(f"  [post] Scraping: {post_url}")
    safe_get(driver, post_url)

    # --- Expand all collapsed / paginated comments -------------------------
    expand_hidden_comments(driver)

    # --- Parse the fully-rendered page with BeautifulSoup ------------------
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # --- Post metadata -----------------------------------------------------
    title_tag = soup.select_one("a.title")
    title = title_tag.get_text(strip=True) if title_tag else "(no title)"

    author_tag = soup.select_one("p.tagline a.author")
    author = author_tag.get_text(strip=True) if author_tag else "[deleted]"

    score_tag = soup.select_one("div.score span.number")
    score = score_tag.get_text(strip=True) if score_tag else "0"

    # Self-text (body) of the post, if any (link posts won't have this).
    selftext_tag = soup.select_one("div.usertext-body div.md")
    selftext = selftext_tag.get_text(separator="\n", strip=True) if selftext_tag else ""

    time_tag = soup.select_one("p.tagline time")
    timestamp = time_tag.get("datetime", "") if time_tag else ""

    # --- Parse the comment forest ------------------------------------------
    # The comment area on old.reddit.com is <div class="commentarea">.
    # Top-level comments are direct children of <div class="sitetable nestedlisting">.
    comment_area = soup.select_one("div.commentarea div.sitetable.nestedlisting")
    comments: list[dict] = []
    if comment_area:
        for top_comment in comment_area.find_all(
            "div", class_="comment", recursive=False
        ):
            parsed = parse_comment(top_comment, depth=0)
            if parsed:
                comments.append(parsed)

    return {
        "title": title,
        "author": author,
        "score": score,
        "url": post_url,
        "selftext": selftext,
        "timestamp": timestamp,
        "num_comments": len(comments),  # top-level count; nested are inside
        "comments": comments,
    }


# ---------------------------------------------------------------------------
# Utility: flatten nested comments (optional, for tabular export)
# ---------------------------------------------------------------------------

def flatten_comments(comments: list[dict], post_title: str = "") -> list[dict]:
    """
    Flatten a nested comment tree into a flat list of dicts (one per
    comment) suitable for writing to CSV.  Each dict includes a ``depth``
    field so you can reconstruct the tree later.

    Parameters
    ----------
    comments : list[dict]
        The nested comment list from ``scrape_post()``.
    post_title : str
        The post title to attach to every row for context.

    Returns
    -------
    list[dict]
        Flat list of comment dicts with ``post_title`` and ``depth``.
    """
    flat: list[dict] = []
    for c in comments:
        flat.append({
            "post_title": post_title,
            "author": c["author"],
            "body": c["body"],
            "score": c["score"],
            "timestamp": c["timestamp"],
            "permalink": c["permalink"],
            "depth": c["depth"],
        })
        # Recurse into replies
        if c.get("replies"):
            flat.extend(flatten_comments(c["replies"], post_title))
    return flat


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """
    CLI entry point.  Parses arguments, launches the browser, scrapes
    the subreddit, and writes the results to a timestamped JSON file
    (and optionally a flat CSV of all comments).
    """
    # --- Argument parsing --------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Scrape a Reddit subreddit's posts and nested comments."
    )
    parser.add_argument(
        "--subreddit", "-s",
        default=DEFAULT_SUBREDDIT,
        help="Name of the subreddit to scrape (default: %(default)s).",
    )
    parser.add_argument(
        "--max-posts", "-n",
        type=int,
        default=10000,
        help="Maximum number of posts to scrape (default: %(default)s).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data",
        help="Directory to write output files into (default: %(default)s).",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also export a flat CSV of all comments.",
    )
    args = parser.parse_args()

    # --- Ensure output directory exists ------------------------------------
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Start the browser -------------------------------------------------
    print("[init] Starting headless Chrome …")
    driver = create_driver()

    try:
        # --- Step 1: collect post URLs from the subreddit listing ----------
        print("scrape_post_urls called")
        post_urls = scrape_post_urls(driver, args.subreddit, args.max_posts)

        # --- Step 2: scrape each post and its comments ---------------------
        all_posts: list[dict] = []
        for i, url in enumerate(post_urls, start=1):
            print(f"[progress] Post {i}/{len(post_urls)}")
            post_data = scrape_post(driver, url)
            all_posts.append(post_data)

        # --- Step 3: write results to JSON ---------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(
            args.output_dir,
            f"../data/reddit_r{args.subreddit}_{timestamp}.json",
        )
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        print(f"[done] Saved {len(all_posts)} posts → {json_path}")

        # --- Step 4 (optional): write flat CSV -----------------------------
        if args.csv:
            import csv

            csv_path = os.path.join(
                args.output_dir,
                f"../data/reddit_r{args.subreddit}_comments_{timestamp}.csv",
            )
            all_flat: list[dict] = []
            for post in all_posts:
                all_flat.extend(
                    flatten_comments(post["comments"], post["title"])
                )

            if all_flat:
                fieldnames = all_flat[0].keys()
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_flat)
                print(f"[done] Saved {len(all_flat)} comments → {csv_path}")

    finally:
        # Always close the browser, even if something crashes.
        driver.quit()
        print("[cleanup] Browser closed.")


if __name__ == "__main__":
    main()
