# Open file
import json

with open("./r_CryptoScams_comments_2025-2026.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

# Filter for keywords ("romance scam", "pig butchering")
keywords = {"romance scam", "pig butchering"}

def comment_matches(comment):
    text = " ".join([
        comment.get("body", ""),
    ]).lower()

    return any(kw in text for kw in keywords)

filtered_comments = [comment for comment in data if comment_matches(comment) and "[deleted]" not in 
                  comment.get("body", "").lower()
                  and "removed" not in comment.get("body", "").lower()
                  and comment.get("body", "").strip() != ""
                  ]

with open("./filtered_CryptoScams_comments_2025-2026.jsonl", "w", encoding="utf-8") as f:
    for comment in filtered_comments:
        f.write(json.dumps(comment) + "\n")
