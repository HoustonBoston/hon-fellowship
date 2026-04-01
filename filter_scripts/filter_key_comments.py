# Open file
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser(description="Filter Reddit posts for specific keywords.")
parser.add_argument("--keywords", "-k", nargs="+", default=["romance scam", "pig butchering"], help="Keywords to filter posts by")
parser.add_argument("--file", "-f", help="Input file path", required=True)
args = parser.parse_args()

path = Path(args.file)

# Filter for keywords ("romance scam", "pig butchering")
keywords = set(args.keywords)

def comment_matches(comment):
    text = " ".join([
        comment.get("body", ""),
    ]).lower()

    return any(kw in text for kw in keywords)

# Using yield to read file line by line and parse JSON CRAZY effiently.
def extract_json_line(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def format_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%B %d, %Y %H:%M:%S UTC") if ts else None

#ex: if path.name is r_CryptoScams_2020-2025_comments.jsonl, filename will be CryptoScams
filename = path.name.split(".")[0].split('_')[1]
print("filename:", filename)
output_dir = Path(__file__).resolve().parent.parent / filename / "data"  
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / f"filtered_{path.name}", "w", encoding="utf-8") as f:
    comments = extract_json_line(path)
    for comment in comments:
        if(comment_matches(comment)):
            filtered_comment = {
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
            } if comment.get("body", "").strip() != "" else None
            if filtered_comment is not None:
                f.write(json.dumps(filtered_comment) + "\n")
