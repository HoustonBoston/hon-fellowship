# Open file
import argparse
import json
from datetime import datetime, timezone

with open("./data/r_CryptoScams2020-2025_comments.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

parser = argparse.ArgumentParser(description="Filter Reddit posts for specific keywords.")
parser.add_argument("--keywords", "-k", nargs="+", default=["romance scam", "pig butchering"], help="Keywords to filter posts by")
args = parser.parse_args()

# Filter for keywords ("romance scam", "pig butchering")
keywords = set(args.keywords)

def comment_matches(comment):
    text = " ".join([
        comment.get("body", ""),
    ]).lower()

    return any(kw in text for kw in keywords)

def format_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%B %d, %Y %H:%M:%S UTC") if ts else None

filtered_comments = [
    {
        "id": comment.get("id"),
        "body": comment.get("body"),
        "date": format_date(comment.get("created_utc")),
        "ups": comment.get("ups"),
        "downs": comment.get("downs"),
        "parent_id": comment.get("parent_id"),
        "subreddit": comment.get("subreddit"),
        "author": comment.get("author"),
        "actual_post_id": comment.get("link_id")[3:] if comment.get("link_id") 
        else None,
    }
    for comment in data if comment_matches(comment)
    # and "[deleted]" not in comment.get("body", "").lower()
    # and "removed" not in comment.get("body", "").lower()
    and comment.get("body", "").strip() != ""
]

with open("./data/filtered_CryptoScams_2020-2025_comments.jsonl", "w", encoding="utf-8") as f:
    for comment in filtered_comments:
        f.write(json.dumps(comment) + "\n")
