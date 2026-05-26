import requests
import json

url = "http://localhost:8000/analyze"

def test_upload(name, filename, content, content_type):
    print(f"\n--- Testing {name} ---")
    files = {'file': (filename, content, content_type)}
    try:
        r = requests.post(url, files=files)
        print(f"Status Code: {r.status_code}")
        try:
            print(f"Response: {json.dumps(r.json(), indent=2)}")
        except:
            print(f"Response Text: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

# 1. Non-PDF extension
test_upload("Non-PDF Extension", "test.txt", "hello", "text/plain")

# 2. PDF extension, wrong magic bytes
test_upload("Wrong Magic Bytes", "test.pdf", "hello", "application/pdf")

# 3. Correct magic bytes (minimal)
test_upload("Correct Magic Bytes", "test.pdf", b"%PDF-1.1\n%...", "application/pdf")
