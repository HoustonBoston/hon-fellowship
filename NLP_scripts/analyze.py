import ollama
import argparse
import json
import re
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


_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _number_word_to_int(token: str):
    return _NUMBER_WORDS.get(token.lower())


def _parse_amount_value(raw_value: str, suffix: str = "") -> float:
    v = float(raw_value.replace(",", ""))
    if suffix.lower() == "k":
        v *= 1_000
    elif suffix.lower() == "m":
        v *= 1_000_000
    return v


def _find_currency_amounts(text: str):
    """
    Return all explicit money amounts found in text as floats.
    Handles patterns like:
    - $37,700
    - 30k USD
    - USD 1.5 million
    - 5000USDT
    """
    lower_text = text.lower()
    amounts = []

    # 1) Dollar-sign first patterns, optionally with k/m suffix.
    for m in re.finditer(r"\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)(?:\s*([kKmM]))?", text):
        amounts.append(_parse_amount_value(m.group(1), m.group(2) or ""))

    # 2) Currency code with value patterns.
    code_pattern = re.compile(
        r"\b(?:usd|cad|usdt|eur|gbp|aud|inr)\s*(\d+(?:,\d{3})*(?:\.\d+)?)(?:\s*([kKmM]))?\b",
        re.IGNORECASE,
    )
    for m in code_pattern.finditer(text):
        amounts.append(_parse_amount_value(m.group(1), m.group(2) or ""))

    # 3) Value followed by currency code patterns.
    reverse_code_pattern = re.compile(
        r"\b(\d+(?:,\d{3})*(?:\.\d+)?)(?:\s*([kKmM]))?\s*(?:usd|cad|usdt|eur|gbp|aud|inr)\b",
        re.IGNORECASE,
    )
    for m in reverse_code_pattern.finditer(text):
        amounts.append(_parse_amount_value(m.group(1), m.group(2) or ""))

    # 4) Bare k/m patterns only when near loss words to reduce false positives.
    bare_km_pattern = re.compile(r"\b(\d+(?:\.\d+)?)\s*([kKmM])\b")
    for m in bare_km_pattern.finditer(text):
        start, end = m.span()
        window = lower_text[max(0, start - 45): min(len(lower_text), end + 45)]
        if any(token in window for token in ["lost", "loss", "down", "scam", "stuck", "invested"]):
            amounts.append(_parse_amount_value(m.group(1), m.group(2)))

    return amounts


def _extract_final_total_statement(text: str):
    """
    Prefer explicit self-reported final totals.
    Example: "I ended up losing a total of CAD $37,700"
    """
    pattern = re.compile(
        r"(?:lost|losing|loss|down)\s+(?:a\s+total\s+of\s+)?(?:about\s+|around\s+|approx(?:imately)?\s+|~\s*)?"
        r"(?:(?:usd|cad|usdt|eur|gbp|aud|inr)\s*)?\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)(?:\s*([kKmM]))?",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    last = matches[-1]
    return _parse_amount_value(last.group(1), last.group(2) or "")


def _sum_investments_minus_withdrawals(text: str):
    """
    Heuristic for narratives that state deposits and partial recoveries.
    Computes: sum(invest-like amounts) - sum(withdraw-like amounts)
    in local sentence windows.
    """
    sentence_split = re.split(r"(?<=[.!?])\s+", text)
    invested_total = 0.0
    withdrawn_total = 0.0

    invest_words = ["invest", "put", "depos", "sent", "wire", "transferred", "liquidated"]
    withdraw_words = ["withdrew", "withdraw", "got back", "returned", "cash out", "pulled out"]

    for sent in sentence_split:
        amounts = _find_currency_amounts(sent)
        if not amounts:
            continue
        s_lower = sent.lower()
        if any(w in s_lower for w in invest_words):
            invested_total += sum(amounts)
        if any(w in s_lower for w in withdraw_words):
            withdrawn_total += sum(amounts)

    net = invested_total - withdrawn_total
    return net if net > 0 else None


def extract_total_loss_rule_based(title: str, selftext: str):
    """
    Deterministically estimate total loss.
    Returns an integer string or "unknown".
    """
    text = f"{title}\n\n{selftext}"

    # 1) strongest signal: explicit final loss statement
    final_total = _extract_final_total_statement(text)
    if final_total is not None and final_total > 0:
        return str(int(round(final_total)))

    # 2) next signal: compute from deposits and withdrawals
    net = _sum_investments_minus_withdrawals(text)
    if net is not None and net > 0:
        return str(int(round(net)))

    # 3) final fallback: largest amount in loss-oriented context
    amounts = _find_currency_amounts(text)
    if amounts:
        return str(int(round(max(amounts))))

    return "unknown"
    
def extract_technique_and_total_dollar_lost(path, args):
    with open(str(path.resolve().with_suffix("")) + "_with_technique.jsonl", "w", encoding="utf-8") as f:
        for post_or_comment in extract_json_line(path):
            # stringify the JSON object for context
            question = f"{args.question}\n\nData: Title: {post_or_comment['title']}, Text: {post_or_comment['selftext']}"
            answer = ask_ollama(question, model=args.model)
            # get rid of special chars at the end
            answer = answer.rstrip(".").rstrip("*").lstrip("*")
            post_or_comment['technique'] = answer

            # Use deterministic parsing for total loss to avoid LLM arithmetic hallucinations.
            post_or_comment['total_loss'] = extract_total_loss_rule_based(
                title=post_or_comment.get('title', ''),
                selftext=post_or_comment.get('selftext', ''),
            )

            f.write(json.dumps(post_or_comment, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    """Takes args from command line and passes them to the ask_ollama function."""
    parser = argparse.ArgumentParser(description="Custom params for ask_ollama function.")
    parser.add_argument("--question", "-q", type=str, required=True, help="The question to ask Ollama.")
    parser.add_argument("--model", "-m", type=str, default="llama3:8b", help="The Ollama model to use (default: llama3:8b).")
    parser.add_argument("--file", "-f", type=str, help="Path to a file containing some data", required=True)
    args = parser.parse_args()

    path = Path(args.file)
    extract_technique_and_total_dollar_lost(path, args=args)
            
