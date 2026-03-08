# Open file
import json
from datetime import datetime, timezone
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description="Filter Reddit posts for specific keywords.")
parser.add_argument("--keywords", "-k", nargs="+", default=["romance scam", "pig butchering"], help="Keywords to filter posts by")
parser.add_argument("--input", "-i", help="Input file path", required=True)
args = parser.parse_args()

path = Path(args.input)

# Filter for keywords ("romance scam", "pig butchering")
keywords = set(args.keywords)

# Using yield to read file line by line and parse JSON effiently.
def extract_json_line(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def post_matches(post):
    text = " ".join([
        post.get("title", ""),
        post.get("selftext", ""),
    ]).lower()

    return any(kw in text for kw in keywords)

def format_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%B %d, %Y %H:%M:%S UTC") if ts else None


#ex: if path.name is r_CryptoScams_2020-2025_posts.jsonl, filename will be CryptoScams
filename = path.name.split(".")[0].split('_')[1]
# parent of this file
output_dir = Path(__file__).resolve().parent.parent / filename / "data"  
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / f"filtered_{path.name}", "w", encoding="utf-8") as f:
    posts = extract_json_line(path)
    for post in posts:
        if (
            post_matches(post)
            and "[deleted]" not in post.get("title", "").lower()
            and "[deleted]" not in post.get("selftext", "").lower()
            and "removed" not in post.get("title", "").lower()
            and "removed" not in post.get("selftext", "").lower()
            and post.get("title", "").strip() != ""
            and post.get("selftext", "").strip() != ""
            ):
            filtered_post = {
                "id": post.get("id"),
                "subreddit": post.get("subreddit"),
                "title": post.get("title"),
                "selftext": post.get("selftext"),
                "date": format_date(post.get("created_utc")),
                "ups": post.get("ups"),
                "downs": post.get("downs"),
            }
            f.write(json.dumps(filtered_post) + "\n")
