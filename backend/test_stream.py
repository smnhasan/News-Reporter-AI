import requests
import time

url = "http://localhost:8000/api/chat/stream?query=Hi"
start_time = time.time()
with requests.get(url, stream=True) as r:
    for line in r.iter_lines():
        if line:
            elapsed = time.time() - start_time
            print(f"[{elapsed:.2f}s] {line.decode('utf-8')}")
