import ollama
import argparse
import json
from pathlib import Path
import os

########################
#
# Extracts technique from each post or comment using the ask_ollama function 
# and saves the results to a new JSONL file.
#
########################

DEFAULT_QUESTION = "Classify the scenario into exactly one category that best fits from this list: " \
                     "[impersonation, investment, romance, grooming, social engineering] " \
                     "Output only the category name. Do not include punctuation or explanations. " \
                     "Category: "


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
        os.exit(1)

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
            question = f"Scenario: title: {post_or_comment['title']}, text: {post_or_comment['selftext']}\n\n{args.question}"
            answer = ask_ollama(question, model=args.model)
            # get rid of special chars at the end
            answer = answer.strip().rstrip(".").rstrip("*").lstrip("*").lower()
            post_or_comment['technique'] = answer
            f.write(json.dumps(post_or_comment, ensure_ascii=False) + "\n")
