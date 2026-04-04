import ollama

def ask_ollama(question: str, model: str = "qwen3.5:35b") -> str:
    response = ollama.chat(model=model, 
                           messages=[
                               {
                                   "role": "user", 
                                   "content": question
                            }])
    # return the assistant message content when available
    return response

if __name__ == "__main__":
    print(ask_ollama("What is today's date in MM/DD/YYYY format?"))
