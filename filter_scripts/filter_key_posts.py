# Open file
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import argparse
from posixpath import relpath

parser = argparse.ArgumentParser(description="Filter Reddit posts for specific keywords.")
parser.add_argument("--keywords", "-k", nargs="+", default=["romance scam", "pig butchering"], help="Keywords to filter posts by")
parser.add_argument("--input", "-i", default="r_CryptoScams2020-2025_posts.jsonl", help="Input file path")
args = parser.parse_args()

path = Path(args.input)

# Filter for keywords ("romance scam", "pig butchering")
keywords = set(args.keywords)

with open(path, "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

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


#ex: if path.name is r_CryptoScams_2020-2025_posts.jsonl, filename will be CryptoScams
filename = path.name.split(".")[0].split('_')[1]
# parent of this file
output_dir = Path(__file__).resolve().parent.parent / filename / "data"  
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / f"filtered_{path.name}", "w", encoding="utf-8") as f:
    for post in filtered_posts:
        f.write(json.dumps(post) + "\n")
