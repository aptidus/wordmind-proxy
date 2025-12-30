import os
from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

UPSTREAM = "https://magic.wordmind.ai"
PROXY_AUTH = os.environ.get("PROXY_AUTH", "")
TYPINGMIND_API_KEY = os.environ.get("TYPINGMIND_API_KEY", "")

# Accept POST for any path, with or without trailing slash
@app.api_route("/{path:path}", methods=["POST"])
async def proxy(path: str, request: Request):
    auth = request.headers.get("x-proxy-auth", "")
    if not PROXY_AUTH or auth != PROXY_AUTH:
        return Response(content="Unauthorized", status_code=401)

    if not TYPINGMIND_API_KEY:
        return Response(content="Missing TYPINGMIND_API_KEY on proxy", status_code=500)

    body = await request.body()

    # Build upstream URL explicitly and avoid any redirect rewrite
    upstream_url = f"{UPSTREAM}/{path}".replace("//api/", "/api/")  # minor safety
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": TYPINGMIND_API_KEY,
    }

    timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        r = await client.post(upstream_url, content=body, headers=headers)

    # Pass through response content + content-type
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json"),
    )

# Optional GET for health / DNS test (prevents 307 surprises on base URL)
@app.get("/")
async def health():
    return {"ok": True}
