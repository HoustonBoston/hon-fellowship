import ollama

def ask_ollama(question: str, model: str = "qwen3.5:35b") -> str:
    response = ollama.chat(model, question)
    return response

if __name__ == "__main__":
    print(ask_ollama("What is today's date in USA format?"))
