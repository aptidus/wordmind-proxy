import os
from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

UPSTREAM = "https://magic.wordmind.ai"
PROXY_AUTH = os.environ.get("PROXY_AUTH", "")
TYPINGMIND_API_KEY = os.environ.get("TYPINGMIND_API_KEY", "")

@app.post("/{path:path}")
async def proxy(path: str, request: Request):
    # Shared secret auth from Hugging Face
    auth = request.headers.get("x-proxy-auth", "")
    if not PROXY_AUTH or auth != PROXY_AUTH:
        return Response(content="Unauthorized", status_code=401)

    if not TYPINGMIND_API_KEY:
        return Response(content="Missing TYPINGMIND_API_KEY on proxy", status_code=500)

    body = await request.body()
    upstream_url = f"{UPSTREAM}/{path}"
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": TYPINGMIND_API_KEY,
    }

    timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(upstream_url, content=body, headers=headers)
        return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))
