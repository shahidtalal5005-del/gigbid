import requests
from typing import List

def get_embedding(text: str) -> List[float]:
    """Generate embeddings using the local Ollama container running nomic-embed-text."""
    url = "http://localhost:11434/api/embed"
    payload = {
        "model": "nomic-embed-text",
        "input": text
    }
    
    try:
        response = requests.post(url, json=payload)
        
        # If it fails, print the exact message from Ollama instead of a generic 404
        if response.status_code != 200:
            print(f"Ollama API Error: {response.status_code} - {response.text}")
            return []
            
        # The modern /api/embed endpoint returns a list of embeddings
        return response.json()["embeddings"][0]
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Ollama. Is the Docker container running?")
        return []
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

if __name__ == "__main__":
    test_text = "I am an expert in Python and backend development."
    print("Testing connection to local Ollama (nomic-embed-text)...")
    
    vector = get_embedding(test_text)
    
    if vector:
        print(f"\n✅ Success! Generated a vector with {len(vector)} dimensions.")
        print(f"First 5 values: {vector[:5]}")
    else:
        print("\n❌ Failed to generate embedding.")