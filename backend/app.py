"""
FastAPI application entrypoint for the Website Knowledge Module.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.routes import router as api_router
from routes.chat import router as chat_router
from config import settings
from utils.exceptions import WebsiteKnowledgeError

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(WebsiteKnowledgeError)
async def website_error_handler(_: Request, exc: WebsiteKnowledgeError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Website Knowledge RAG</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.5; color: #1f2937; }
          code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }
          a { color: #2563eb; }
        </style>
      </head>
      <body>
        <h1>Website Knowledge RAG</h1>
        <p>The Website Knowledge Module API is running.</p>
        <p>Open <a href="/docs">/docs</a>, <a href="/redoc">/redoc</a>, or <a href="/openapi.json">/openapi.json</a>.</p>
        <h2>Endpoints</h2>
        <ul>
          <li><code>POST /crawl</code></li>
          <li><code>POST /index</code></li>
          <li><code>POST /retrieve</code></li>
          <li><code>GET /websites</code></li>
          <li><code>DELETE /website/{website_id}</code></li>
          <li><code>PUT /refresh</code></li>
          <li><code>GET /statistics</code></li>
          <li><code>GET /health</code></li>
        </ul>
      </body>
    </html>
    """


app.include_router(health_router)
app.include_router(api_router)
app.include_router(chat_router)
