import ollama

def ask_ollama(question: str, model: str = "llama3:8b") -> str:
    try:
        response = ollama.chat(model=model, 
                            messages=[
                                {
                                    "role": "user", 
                                    "content": question
                                }])
        # return the assistant message content when available
        return response['Message']['Content']
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Sorry, I couldn't process your request."

if __name__ == "__main__":
    print(ask_ollama("What is today's date in MM/DD/YYYY format?"))
