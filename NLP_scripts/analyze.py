import ollama
import argparse
import json
from pathlib import Path


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
                                    "role": "user", 
                                    "content": question
                                }],
                                options={
                                    "temperature": 0.4
                                })
        # return the assistant message content when available
        return response['message']['content']
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Sorry, I couldn't process your request."

if __name__ == "__main__":
    """Takes args from command line and passes them to the ask_ollama function."""
    parser = argparse.ArgumentParser(description="Custom params for ask_ollama function.")
    parser.add_argument("--question", "-q", type=str, required=True, help="The question to ask Ollama.")
    parser.add_argument("--model", "-m", type=str, default="llama3:8b", help="The Ollama model to use (default: llama3:8b).")
    parser.add_argument("--file", "-f", type=str, help="Path to a file containing some data", required=True)
    args = parser.parse_args()

    path = Path(args.file)

    for post_or_comment in extract_json_line(path):
        # stringify the JSON object for context
        question = f"{args.question}\n\nData: {json.dumps(post_or_comment, ensure_ascii=False)}"
        answer = ask_ollama(question, model=args.model)
        # get rid of period at the end
        answer = answer.rstrip(".")
        print(f"Question: {question}\nAnswer: {answer}\n{'-'*50}\n")

