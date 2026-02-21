from __future__ import annotations

from html import escape
import os
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.services.analyzer import analyze_text, merge_issues, normalize_glm_issues
from app.services.glm_client import GLMClient
from app.services.parser import parse_file_bytes


DEFAULT_GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_GLM_MODEL = "glm-4.6v"
DEFAULT_GLM_TIMEOUT_SECONDS = 15
DEFAULT_GLM_MAX_SENTENCES = 120
DEFAULT_GLM_MAX_TOTAL_CHARS = 18000
DEFAULT_GLM_MAX_SENTENCE_CHARS = 400
DEFAULT_FRONTEND_URL = "https://keji060822.github.io/paper-consistency-platform/"


def _split_origins(csv_text: str) -> list[str]:
    return [item.strip() for item in csv_text.split(",") if item.strip()]


def _to_int_env(name: str, default_value: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default_value
    try:
        value = int(raw)
    except ValueError:
        return default_value
    return value if value > 0 else default_value


def _build_glm_input_sentences(sentences: list[dict[str, str]]) -> list[dict[str, str]]:
    max_sentences = _to_int_env("GLM_MAX_SENTENCES", DEFAULT_GLM_MAX_SENTENCES)
    max_total_chars = _to_int_env("GLM_MAX_TOTAL_CHARS", DEFAULT_GLM_MAX_TOTAL_CHARS)
    max_sentence_chars = _to_int_env("GLM_MAX_SENTENCE_CHARS", DEFAULT_GLM_MAX_SENTENCE_CHARS)

    selected: list[dict[str, str]] = []
    total_chars = 0
    for idx, item in enumerate(sentences):
        sid = str(item.get("id", f"s-{idx + 1}")).strip() or f"s-{idx + 1}"
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        clipped = text[:max_sentence_chars]
        projected_chars = total_chars + len(clipped)
        if selected and projected_chars > max_total_chars:
            break
        selected.append({"id": sid, "text": clipped})
        total_chars = projected_chars
        if len(selected) >= max_sentences:
            break
    return selected


DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:8090",
    "http://localhost:8090",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://keji060822.github.io",
    "null",
]

runtime_origins = _split_origins(os.getenv("CORS_ALLOW_ORIGINS", ""))
cors_origins = sorted(set(DEFAULT_CORS_ORIGINS + runtime_origins))

app = FastAPI(title="Paper Consistency Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    frontend_url = escape(os.getenv("FRONTEND_URL", DEFAULT_FRONTEND_URL), quote=True)
    return f"""<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
    <title>论文一致性检测 API</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f7f9fc;
        --surface: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --primary: #2563eb;
        --border: #e2e8f0;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Segoe UI", Arial, sans-serif;
        color: var(--text);
        background: linear-gradient(180deg, #ffffff, var(--bg));
      }}
      .wrap {{
        max-width: 760px;
        margin: 48px auto;
        padding: 0 20px;
      }}
      .card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: 1.75rem;
      }}
      p {{
        margin: 0;
        color: var(--muted);
      }}
      .actions {{
        margin-top: 18px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }}
      a.btn {{
        text-decoration: none;
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid var(--border);
        color: var(--text);
        background: #fff;
        font-weight: 600;
      }}
      a.btn.primary {{
        background: var(--primary);
        border-color: var(--primary);
        color: #fff;
      }}
      code {{
        background: #eef2ff;
        padding: 2px 6px;
        border-radius: 6px;
        color: #1d4ed8;
      }}
      ul {{
        margin: 14px 0 0;
        padding-left: 18px;
      }}
    </style>
  </head>
  <body>
    <main class=\"wrap\">
      <section class=\"card\">
        <h1>论文一致性检测 API</h1>
        <p>后端服务运行中。可通过下方入口查看文档、健康状态和前端页面。</p>
        <div class=\"actions\">
          <a class=\"btn primary\" href=\"/docs\">打开 API 文档</a>
          <a class=\"btn\" href=\"/health\">健康检查</a>
          <a class=\"btn\" href=\"{frontend_url}\" target=\"_blank\" rel=\"noreferrer\">打开前端页面</a>
        </div>
        <ul>
          <li>分析接口: <code>POST /api/analyze</code></li>
          <li>状态接口: <code>GET /health</code></li>
        </ul>
      </section>
    </main>
  </body>
</html>"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    base_url: str = Form(DEFAULT_GLM_BASE_URL),
    model: str = Form(DEFAULT_GLM_MODEL),
    api_key: str = Form(""),
) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = parse_file_bytes(file.filename or "uploaded.txt", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in uploaded file.")

    result = analyze_text(text)

    runtime_api_key = api_key.strip() or os.getenv("GLM_API_KEY", "").strip()
    glm_used = False
    glm_attempted = False
    glm_error = ""
    glm_timeout_seconds = _to_int_env("GLM_TIMEOUT_SECONDS", DEFAULT_GLM_TIMEOUT_SECONDS)
    glm_input_sentences = 0
    if runtime_api_key:
        glm_attempted = True
        try:
            review_sentences = _build_glm_input_sentences(result["sentences"])
            glm_input_sentences = len(review_sentences)
            if review_sentences:
                client = GLMClient(
                    api_key=runtime_api_key,
                    base_url=base_url,
                    model=model,
                    timeout=glm_timeout_seconds,
                )
                raw_glm_issues = client.review(review_sentences)
                glm_issues = normalize_glm_issues(raw_glm_issues)
                if glm_issues:
                    result["issues"] = merge_issues(result["issues"], glm_issues)
                    glm_used = True
        except Exception as exc:  # pragma: no cover - protective fallback
            glm_error = str(exc).strip()[:200]

    result["source"] = "hybrid" if glm_used else "heuristic"
    result["engine"] = {
        "glm_enabled": bool(runtime_api_key),
        "glm_attempted": glm_attempted,
        "glm_used": glm_used,
        "glm_timeout_seconds": glm_timeout_seconds,
        "glm_input_sentences": glm_input_sentences,
        "glm_error": glm_error,
        "base_url": base_url,
        "model": model,
    }
    return result
