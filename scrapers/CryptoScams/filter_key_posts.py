# Open file
import json
from datetime import datetime, timezone

with open("./r_CryptoScams_posts_2025-2026.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

# Filter for keywords ("romance scam", "pig butchering")
keywords = {"romance scam", "pig butchering"}

def post_matches(post):
    text = " ".join([
        post.get("title", ""),
        post.get("selftext", ""),
    ]).lower()

    return any(kw in text for kw in keywords)

def format_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%B %d, %Y %H:%M:%S UTC") if ts else None

filtered_posts = [
    {
        "id": post.get("id"),
        "subreddit": post.get("subreddit"),
        "title": post.get("title"),
        "selftext": post.get("selftext"),
        "date": format_date(post.get("created_utc")),
        "ups": post.get("ups"),
        "downs": post.get("downs"),
    }
    for post in data if post_matches(post)
    and "[deleted]" not in post.get("title", "").lower()
    and "[deleted]" not in post.get("selftext", "").lower()
    and "removed" not in post.get("title", "").lower()
    and "removed" not in post.get("selftext", "").lower()
    and post.get("title", "").strip() != ""
    and post.get("selftext", "").strip() != ""
]

with open("./filtered_CryptoScams_posts_2025-2026.jsonl", "w", encoding="utf-8") as f:
    for post in filtered_posts:
        f.write(json.dumps(post) + "\n")
