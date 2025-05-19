import os
import requests
import time
import json

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

# Available models to try in order (fallback mechanism)
AVAILABLE_MODELS = [
    "mistralai/mistral-7b-instruct",  # First choice - Mistral 7B Instruct
    "google/palm-2-chat-bison",        # Second choice - Palm 2
    "anthropic/claude-instant-v1",     # Third choice - Claude Instant
    "openai/gpt-3.5-turbo"             # Last resort - GPT 3.5 (uses credits)
]

# Headers required for OpenRouter API
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ezlife-taskmanager.com",  # Required for OpenRouter
    "X-Title": "EZLife Task Manager"   # App name
}

def get_time_estimate(description: str, model: str) -> int:
    """
    Helper function to get time estimate from a specific model
    """
    # System prompt to guide the model's response format
    system_prompt = "You are a task time estimation assistant. Respond ONLY with a numerical estimate in minutes for how long the task would take an average person. Give a single number only, no explanations or additional text."
    
    # User prompt with the task description
    user_prompt = f"How many minutes would it take to complete this task: {description}"
    
    # Prepare payload for OpenRouter API (following OpenAI format)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # Low temperature for more consistent responses
        "max_tokens": 10     # We only need a small number
    }
    
    print(f"📡 Requesting estimation from model: {model}")
    
    # Make API request
    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        # Extract the response text from the completion
        text = result["choices"][0]["message"]["content"].strip()
        print(f"📝 Raw response from {model}: {text}")
        
        # Extract numbers from the response
        digits = ''.join(filter(str.isdigit, text))
        if digits:
            minutes = int(digits)
            # Sanity check - if estimate is absurdly high, cap it
            if minutes > 1440:  # More than 24 hours
                minutes = 120    # Cap at 2 hours
            return minutes
    
    # If we reach here, something went wrong
    return None


def estimate_time(description: str) -> int:
    """
    Estimate time required for a task using OpenRouter API.
    
    Args:
        description: The task description
        
    Returns:
        Estimated time in minutes (integer)
    """
    print("🔍 Starting task time estimation for:", description)
    
    # Try estimation with multiple models if needed
    for model in AVAILABLE_MODELS:
        try:
            print(f"🤖 Trying with model: {model}")
            minutes = get_time_estimate(description, model)
            
            if minutes is not None:
                print(f"✅ Successfully estimated {minutes} minutes using {model}")
                return minutes
            
            print(f"⚠️ Model {model} failed to provide a valid estimate. Trying next model...")
            time.sleep(1)  # Small delay before trying the next model
            
        except Exception as e:
            print(f"❌ Error with model {model}: {str(e)}")
            continue
    
    # If all models failed, apply heuristic estimation
    print("🧮 All models failed. Using heuristic estimation...")
    
    # Simple heuristic based on word count
    word_count = len(description.split())
    
    if "meeting" in description.lower() or "call" in description.lower():
        minutes = 30
    elif "email" in description.lower() or "message" in description.lower():
        minutes = 10
    elif word_count <= 3:
        minutes = 15  # Very short task descriptions
    elif word_count <= 8:
        minutes = 30  # Short task descriptions
    elif word_count <= 15:
        minutes = 60  # Medium task descriptions
    else:
        minutes = 90  # Long task descriptions
    
    print(f"⚡ Heuristic estimated {minutes} minutes based on description length and keywords")
    return minutes
