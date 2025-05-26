"""
Test script for OpenRouter API integration
"""
import os
import requests

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# Headers required for OpenRouter API
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ezlife-taskmanager.com",  # Required for OpenRouter
    "X-Title": "EZLife Task Manager",   # App name
    "OpenAI-Organization": "org-ezlifetaskmanager"  # Adding this header sometimes helps
}

def test_api():
    """Test the OpenRouter API with a simple request"""
    print(f"Testing OpenRouter API with key: {OPENROUTER_API_KEY[:10]}...")
    
    # Simple test payload
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        print("Sending request to OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=10)
        
        print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            print(f"API Response: {text}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Exception during API request: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    print(f"API Test {'succeeded' if success else 'failed'}")
