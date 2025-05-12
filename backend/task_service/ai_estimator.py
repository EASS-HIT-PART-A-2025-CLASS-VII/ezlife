import os
import requests

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGINGFACE_API_KEY = os.getenv("HF_TOKEN")

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

def estimate_time(description: str) -> int:
    prompt = f"Estimate duration in minutes for the task: {description}"
    payload = {"inputs": prompt}

    try:
        print("📡 Requesting Hugging Face API...")
        print("🔗 URL:", HUGGINGFACE_API_URL)

        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
        print("🌐 Response Status:", response.status_code)

        if response.status_code == 200:
            result = response.json()
            text = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text")
            minutes = int(''.join(filter(str.isdigit, text))) if text else 30
            print("✅ Estimated Minutes:", minutes)
            return minutes

        elif response.status_code == 404:
            print("❌ Model Not Found - Check URL")
        elif response.status_code == 401:
            print("❌ Unauthorized - Check API Key")
        else:
            print("❌ Unexpected Error:", response.status_code, response.text)

    except Exception as e:
        print("⚠️ AI estimation failed:", e)

    # Fallback if estimation fails
    print("⚡ Using fallback value: 30 minutes")
    return 30
