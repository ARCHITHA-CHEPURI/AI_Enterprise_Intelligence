import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2:1b",
        "prompt": "Say 'Ollama is ready!' in a short sentence.",
        "stream": False
    }
    
    print(f"Testing connection to Ollama at {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        print("Success!")
        print(f"Ollama response: {result.get('response')}")
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Make sure Ollama is running and the model 'llama3.2:1b' is pulled.")

if __name__ == "__main__":
    test_ollama()
