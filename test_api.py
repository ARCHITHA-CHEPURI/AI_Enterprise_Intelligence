import requests
import time
import sys

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    # Wait for server to be up
    print("Waiting for server...")
    for i in range(10):
        try:
            requests.get(base_url)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            print(f"Retry {i+1}...")
    else:
        print("Server failed to start.")
        sys.exit(1)
    
    print("Server is up!")

    # Test Static File
    print("Testing static file serving...")
    resp = requests.get(f"{base_url}/")
    assert resp.status_code == 200
    assert "<title>Enterprise Knowledge Bot</title>" in resp.text
    print("Static file served successfully.")

    # Test Chat Endpoint
    print("Testing /chat endpoint...")
    query = {"query": "What is the earnings report?"}
    try:
        resp = requests.post(f"{base_url}/chat", json=query)
        if resp.status_code == 200:
            data = resp.json()
            print("Response received:")
            print(f"Answer: {data.get('answer')}")
            print(f"Sources: {len(data.get('sources'))}")
            print(f"Accuracy: {data.get('accuracy')}")
            print(f"Precision: {data.get('precision')}")
            print(f"Confidence: {data.get('confidence')}")
            
            assert 'accuracy' in data
            assert 'precision' in data
            assert 'confidence' in data
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()
