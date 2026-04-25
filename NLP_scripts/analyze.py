import ollama
import argparse
import json
from pathlib import Path
import os
import re
import sys

########################
#
# Extracts technique from each post or comment using the ask_ollama function 
# and saves the results to a new JSONL file.
#
########################

ALLOWED_LABELS = [
    "impersonation",
    "investment manipulation",
    "romance",
    "grooming",
    "social engineering",
]

DEFAULT_QUESTION = (
    "Classify the scenario into EXACTLY ONE category from this list: "
    "['impersonation', 'investment manipulation', 'romance', 'grooming', 'social engineering'].\n"
    "Use these definitions:\n"
    "- impersonation: scammer pretends to be a specific person, institution, authority, or support agent.\n"
    "- investment manipulation: fake/rigged investment or trading opportunity, fake returns, fake platform.\n"
    "- romance: emotional/romantic relationship used to build trust before scamming.\n"
    "- grooming: gradual long-term emotional conditioning and dependency building.\n"
    "- social engineering: manipulation tactics that do not fit the above categories.\n\n"
    "Tie-break rules:\n"
    "1) If explicit pretending/fake identity/posing as a known person or organization appears, choose impersonation.\n"
    "2) Else if relationship/dating romance is central, choose romance.\n"
    "3) Else if fake investment/trading is central, choose investment manipulation.\n"
    "4) Else choose the best remaining category.\n\n"
    "Output only one category name, exactly as written in the list. No punctuation, no explanation.\n"
    "Category: "
)

NORMALIZATION_MAP = {
    "impersonation": "impersonation",
    "imposter": "impersonation",
    "imposter scam": "impersonation",
    "identity theft": "impersonation",
    "investment": "investment manipulation",
    "investment scam": "investment manipulation",
    "pig butchering": "investment manipulation",
    "pig-butchering": "investment manipulation",
    "romance": "romance",
    "romance scam": "romance",
    "dating scam": "romance",
    "grooming": "grooming",
    "social engineering": "social engineering",
}


def normalize_label(raw_answer: str, scenario: str) -> str:
    cleaned = raw_answer.strip().lower()
    cleaned = cleaned.strip('"\'`*_.,:;![](){} ')
    cleaned = re.sub(r"\s+", " ", cleaned)

    if cleaned in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[cleaned]

    for label in ALLOWED_LABELS:
        if label in cleaned:
            return label

    scenario_lc = scenario.lower()
    if re.search(
        r"\b(pretend|pretending|impersonat|posing as|fake support|customer service|"
        r"coinbase support|binance support|irs|fbi|police|bank called|official account)\b",
        scenario_lc,
    ):
        return "impersonation"
    if re.search(r"\b(romance|dating|boyfriend|girlfriend|tinder|catfish|love interest)\b", scenario_lc):
        return "romance"
    if re.search(r"\b(investment|trading|profit|returns|defi|forex|exchange|platform)\b", scenario_lc):
        return "investment manipulation"

    return "social engineering"


# Using yield to read file line by line and parse JSON efficiently.
def extract_json_line(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def ask_ollama(question: str, model: str = "llama3:8b") -> str:
    try:
        response = ollama.chat(model=model, 
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are a classification engine. " \
                                    "You must output ONLY the category name. No thoughts, no explanations, no tags."
                                },
                                {
                                    "role": "user", 
                                    "content": question
                                }],
                                options={
                                    "temperature": 0.0,  # Deterministic output
                                    # "num_predict": 10,    # Limit response length
                                    # "stop": ["Scenario"]       # Stop at newline to get concise answers
                                })
        # return the assistant message content when available
        return response['message']['content']
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":

    """Takes args from command line and passes them to the ask_ollama function."""

    parser = argparse.ArgumentParser(description="Custom params for ask_ollama function.")
    parser.add_argument("--question", "-q", type=str, required=False, help="The question to ask Ollama.",
                        default=DEFAULT_QUESTION)
    parser.add_argument("--model", "-m", type=str, default="llama3:8b", help="The Ollama model to use (default: llama3:8b).")
    parser.add_argument("--file", "-f", type=str, help="Path to a file containing some data", required=True)
    args = parser.parse_args()

    path = Path(args.file)
    print(f"Processing file: {path}")
    print(f"question: {args.question}")
    print(f"model: {args.model}")

    with open(str(path.resolve().with_suffix("")) + "_with_technique.jsonl", "w", encoding="utf-8") as f:
        for post_or_comment in extract_json_line(path):
            # stringify the JSON object for context
            title = str(post_or_comment.get('title', ''))
            text = str(post_or_comment.get('selftext', post_or_comment.get('body', '')))
            scenario = f"title: {title}, text: {text}"
            question = f"Scenario: {scenario}\n\n{args.question}"
            raw_answer = ask_ollama(question, model=args.model)
            post_or_comment['technique'] = normalize_label(raw_answer, scenario)
            print(f"scam technique: {post_or_comment['technique']}")
            f.write(json.dumps(post_or_comment, ensure_ascii=False) + "\n")
