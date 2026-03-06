# Open file
import json

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

filtered_posts = [{"title": post.get("title"), "selftext": post.get("selftext")} for post in data if post_matches(post) and "[deleted]" not in 
                  post.get("title", "").lower() and "[deleted]" not in post.get("selftext", "").lower()
                  and "removed" not in post.get("title", "").lower() and "removed" not in post.get("selftext", "").lower()
                  and post.get("title", "").strip() != "" and post.get("selftext", "").strip() != ""
                  ]

with open("./filtered_CryptoScams_posts_2025-2026.jsonl", "w", encoding="utf-8") as f:
    for post in filtered_posts:
        f.write(json.dumps(post) + "\n")
