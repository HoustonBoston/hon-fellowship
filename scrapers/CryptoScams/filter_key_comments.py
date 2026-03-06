# Open file
import json
from datetime import datetime, timezone

with open("./r_CryptoScams_comments_2025-2026.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

# Filter for keywords ("romance scam", "pig butchering")
keywords = {"romance scam", "pig butchering"}

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
    }
    for comment in data if comment_matches(comment)
    and "[deleted]" not in comment.get("body", "").lower()
    and "removed" not in comment.get("body", "").lower()
    and comment.get("body", "").strip() != ""
]

with open("./filtered_CryptoScams_comments_2025-2026.jsonl", "w", encoding="utf-8") as f:
    for comment in filtered_comments:
        f.write(json.dumps(comment) + "\n")
