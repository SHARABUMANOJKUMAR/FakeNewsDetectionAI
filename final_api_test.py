import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    print("\n--- Testing Health Endpoint ---")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")

def test_text_prediction(text, label):
    print(f"\n--- Testing Text Prediction ({label}) ---")
    data = {"text": text}
    r = requests.post(f"{BASE_URL}/predict", json=data)
    print(f"Status: {r.status_code}")
    print(f"Prediction: {r.json().get('prediction')}")
    print(f"Confidence: {r.json().get('confidence')}")

def test_url_prediction(url, label):
    print(f"\n--- Testing URL Prediction ({label}) ---")
    data = {"url": url}
    r = requests.post(f"{BASE_URL}/predict_url", json=data)
    print(f"Status: {r.status_code}")
    print(f"Prediction: {r.json().get('prediction')}")

if __name__ == "__main__":
    try:
        test_health()
        
        # Real news test (trending)
        test_text_prediction("India wins the cricket match by 5 wickets in a thrilling finish.", "REAL")
        
        # Fake news test
        test_text_prediction("Miracle secret cure found: Scientists discover drinking seawater cures all diseases instantly.", "FAKE")
        
        # URL test (BBC - Trusted)
        test_url_prediction("https://www.bbc.com/news/world-asia-68551351", "REAL SOURCE")
        
    except Exception as e:
        print(f"Test failed: {e}")
