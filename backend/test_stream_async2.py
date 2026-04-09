import asyncio
import httpx
import time

async def main():
    start = time.time()
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("GET", "http://localhost:8000/api/chat/stream?query=Hi") as r:
            async for line in r.aiter_lines():
                if line:
                    print(f"[{time.time()-start:.2f}s] {line}")

asyncio.run(main())
