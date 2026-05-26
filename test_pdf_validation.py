import requests
import io

url = "http://localhost:8000/analyze"

# 1. Test with non-PDF extension
print("Testing non-PDF extension...")
files = {'file': ('test.txt', 'this is not a pdf', 'text/plain')}
try:
    r = requests.post(url, files=files)
    print(f"Status: {r.status_code}, Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")

# 2. Test with PDF extension but wrong magic bytes
print("\nTesting PDF extension with wrong magic bytes...")
files = {'file': ('test.pdf', 'this is not a pdf', 'application/pdf')}
try:
    r = requests.post(url, files=files)
    print(f"Status: {r.status_code}, Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")

# 3. Test with real PDF magic bytes (minimal valid PDF header)
print("\nTesting minimal PDF magic bytes...")
files = {'file': ('test.pdf', b'%PDF-1.4\n%...', 'application/pdf')}
try:
    r = requests.post(url, files=files)
    print(f"Status: {r.status_code}, Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")
