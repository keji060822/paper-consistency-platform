# Paper Consistency Platform (MVP)

This folder now contains:

- `index.html` + `styles.css` + `app.js` (frontend UI)
- `api/` (FastAPI backend)

## 1) Create local virtual environment + install dependencies

```bash
cd paper-consistency-platform-preview
python -m venv .venv
.venv\Scripts\python -m pip install -r api/requirements.txt
```

## 2) Configure GLM key (server-side only)

An `.env` file under `api/` is used by backend runtime.

Windows PowerShell (manual update if needed):

```powershell
$env:GLM_API_KEY="your_real_glm_api_key"
```

If `GLM_API_KEY` is not set, the backend still works with heuristic analysis.

## 3) Run backend

```bash
cd paper-consistency-platform-preview
.\start-backend.ps1
```

## 4) Run frontend

```powershell
cd paper-consistency-platform-preview
.\start-frontend.ps1
```

Health check:

- `http://127.0.0.1:8000/health`

## 5) One-click run (both services)

```powershell
cd paper-consistency-platform-preview
.\start-all.ps1
```

- `http://127.0.0.1:8090`

Make sure **Backend API URL** in UI is:

- `http://127.0.0.1:8000`

Stop all:

```powershell
.\stop-all.ps1
```

## 6) Current scope

- Upload and analyze file via backend `/api/analyze`
- Basic parsing support:
  - `.txt/.tex` direct text decode
  - `.docx` via `python-docx`
  - `.pdf` via `pypdf`
- Issue categories:
  - `term`
  - `logic`
  - `citation_figure`
- Interactive sentence highlighting and report export

## 7) Deploy backend (Render)

This repo includes `render.yaml` for one-click backend deployment.

1. Open:
   - `https://render.com/deploy?repo=https://github.com/keji060822/paper-consistency-platform`
2. Create web service from blueprint.
3. Set env var:
   - `GLM_API_KEY=<your_key>`
4. Wait until service status is `Live`, then copy URL like:
   - `https://paper-consistency-platform-api.onrender.com`

Health check:

- `https://paper-consistency-platform-api.onrender.com/health`
