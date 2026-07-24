import urllib.request
import sys

url = "http://127.0.0.1:8000/api/transactions/1/generate_receipt/"
try:
    response = urllib.request.urlopen(url)
    data = response.read()
    with open("test_download.pdf", "wb") as f:
        f.write(data)
    print(f"Success! Downloaded {len(data)} bytes.")
except Exception as e:
    print(f"Error: {e}")
