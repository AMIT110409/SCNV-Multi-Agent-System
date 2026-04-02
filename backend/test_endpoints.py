import requests
import json

try:
    print("Testing /api/network/map...")
    # NOTE: Normally requires a valid JWT but let's see if we get a 401 or a 500
    res = requests.get("http://127.0.0.1:8000/api/network/map")
    print("Map Route Status:", res.status_code)
    print("Map Route Response:", res.text)
except Exception as e:
    print("Map Test Failed:", e)

try:
    print("\nTesting /api/chat...")
    res = requests.post("http://127.0.0.1:8000/api/chat/", json={"message": "hello"})
    print("Chat Route Status:", res.status_code)
    print("Chat Route Response:", res.text)
except Exception as e:
    print("Chat Test Failed:", e)
