# ScholarAI

ScholarAI is an evidence-backed scholarship discovery application. It accepts a
student profile, optional public profile URLs, and optional PDF documents, then
runs a multi-agent workflow to:

1. Normalize and validate the student profile.
2. Search scholarship and university-funding opportunities in Canada, Germany,
   and Singapore.
3. Extract evidence from opportunity pages.
4. Audit eligibility conservatively.
5. Rank up to five eligible opportunities.
6. Review the shortlist with Groq.
7. Generate a grounded application draft with Gemini.

The application is evidence-backed: definite contradictions are reported as
`does_not_meet`, while genuinely missing or incomparable mandatory evidence is
reported as `unknown`. Verified program alignment can qualify a result when no
mandatory requirement contradicts the profile.

## Live deployment

The frontend and backend are deployed separately:

- Frontend: <https://findscholarship.vercel.app/>
- Backend API: <https://scholarai-amsd.onrender.com/>

Useful live endpoints:

- Frontend dashboard: <https://findscholarship.vercel.app/>
- Backend service information: <https://scholarai-amsd.onrender.com/>
- Health: <https://scholarai-amsd.onrender.com/health>
- API documentation: <https://scholarai-amsd.onrender.com/docs>

The Vercel frontend calls the Render API using `VITE_API_BASE_URL`. The
production default is `https://scholarai-amsd.onrender.com`. FastAPI allows
the Vercel origin through explicit CORS configuration.

## Current architecture

The project has a Python/FastAPI backend and a separate Vite React frontend.
Vercel serves the frontend, while Render runs the FastAPI API.

```text
Student browser
  |
  | Loads React app from Vercel
  v
Vercel frontend (frontend/src/App.jsx)
  |
  | POST/GET https://scholarai-amsd.onrender.com
  v
FastAPI API (app/api.py)
  |
  v
LangGraph workflow
  |-- Gemini: profile extraction, evidence extraction, application draft
  |-- Tavily: web search and page extraction
  |-- local MCP server: provider tools over stdio
  |-- Groq: shortlist review
  |-- LangSmith: optional tracing
  v
Results rendered in the Vercel dashboard
```

Important directories:

```text
app/
  agents/          Workflow agent implementations
  api.py           FastAPI application and HTTP endpoints
  graph.py         LangGraph workflow wiring
  jobs.py          In-memory background job execution
  mcp_client.py    Workflow-side MCP client
  mcp_server.py    Local MCP tool server
  tools.py         Gemini, Tavily, PDF, and profile integrations
tests/             Pytest test suite
example.env        Environment variable template
```

## Requirements

- Python 3.12 or newer
- API keys for Google Gemini, Tavily, and Groq
- Optional LangSmith API key for tracing

## Run locally

### 1. Create and activate a virtual environment

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

Using `uv` from the backend directory:

```powershell
Set-Location app
uv sync
```

Using pip:

```powershell
Set-Location app
python -m pip install -e .
python -m pip install pytest
```

### 3. Configure environment variables

Copy `example.env` to `.env` and replace the placeholders:

```powershell
Copy-Item example.env .env
```

`.env`:

```dotenv
TAVILY_API_KEY=your-tavily-key
GOOGLE_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-3.5-flash-lite
GROQ_API_KEY=your-groq-key
GROQ_MODEL=openai/gpt-oss-20b

# Optional LangSmith tracing
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=ScholarAI
```

Do not commit `.env` or paste API keys into source code. The repository ignores
`.env` by default.

### 4. Start the backend and frontend

Start the backend from the `app` directory:

```powershell
Set-Location app
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, start the React frontend:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the dashboard at <http://localhost:5173/>.

The Vite frontend defaults to the deployed Render API. To use the local
backend, create `frontend/.env.local` with:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The interactive API documentation is at <http://127.0.0.1:8000/docs> and the
health check is at <http://127.0.0.1:8000/health>.

The local MCP server is started automatically by the workflow when the Hunter
or Evidence agent calls an MCP tool. Do not start `app/mcp_server.py`
separately for normal application use.

## Using the dashboard

1. Open `http://localhost:5173/`.
2. Complete the structured profile form.
3. Add public profile URLs, such as a GitHub profile.
4. Upload optional PDF files such as a resume or marksheet.
5. Select **Find scholarships**.
6. Review the agent statuses, shortlist, source links, Groq review,
   application draft, and warnings.

Only Canada, Germany, and Singapore are supported destinations. Results are
limited to five recommendations.

## API usage

### Health check

```http
GET /health
```

### Synchronous workflow

```http
POST /workflow
Content-Type: multipart/form-data
```

Fields:

- `profile`: required JSON object string
- `profile_urls`: optional JSON array string, default `[]`
- `documents`: optional PDF files, repeated for multiple files

PowerShell example:

```powershell
$profile = @{
  name = "Rahul"
  degree = "B.Tech CSE"
  cgpa = 8.2
  cgpa_scale = "10"
  preferred_countries = @("Canada", "Germany", "Singapore")
  budget = "low"
} | ConvertTo-Json -Compress

curl.exe -X POST http://127.0.0.1:8000/workflow `
  -F "profile=$profile" `
  -F 'profile_urls=["https://github.com/your-username"]' `
  -F "documents=@resume.pdf"
```

### Background workflow

For the browser dashboard and longer-running requests:

```http
POST /workflow/jobs
GET /workflow/jobs/{job_id}
```

Submit the same multipart fields to `/workflow/jobs`. The response contains a
`job_id` and `status_url`. Poll the status URL until the job is `completed` or
`failed`.

The `profile` JSON must include the core intake fields: name, nationality,
current degree and degree level, graduation status, target degree level,
target field, target intake/year, funding need, and at least one destination
country. The target degree and field are used for research; the current degree
is used for eligibility comparison. Incomplete profiles receive a `422`
response listing the missing fields instead of starting an unreliable search.

While the job is running, the status response includes `current_node`,
`agent_status`, and an `events` array. Each event records the completed
LangGraph node, timestamp, state fields it returned, workflow counts, and any
Supervisor decision. The dashboard renders this chronological execution
timeline rather than relying only on generic stage messages.

Background jobs are currently stored in memory. They are lost when the process
restarts and are not shared between multiple server instances.

## Testing

Run the complete test suite:

```powershell
python -m pytest -q
```

The suite covers the agents, MCP client behavior, API validation, dashboard
serving, background jobs, configuration, observability, and provider failure
paths.

## Deployment

### Backend deployment: Render

Create a Render **Web Service** manually. Do not rely on or push
`render.yaml`; configure the service from the Render dashboard.

| Render field | Value |
|---|---|
| Repository | `UtkarshSingh31/ScholarAI` |
| Branch | Your deployment branch, normally `main` |
| Service name | `scholarai` |
| Language/runtime | `Python 3` |
| Root Directory | `app` |
| Build Command | `pip install --upgrade pip && pip install .` |
| Start Command | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| Instance type | Free for a demo; paid for a continuously available service |
| Health Check Path | `/health` |
| Auto-Deploy | Yes, if you want pushes to deploy automatically |

Set the root directory to `app`. The backend package metadata and Python
modules are inside that directory. Do not use `python main.py`; the correct
ASGI target from the `app` root is `api:app`.

#### Render environment variables

In **Environment → Environment Variables**, add:

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.8` |
| `TAVILY_API_KEY` | Your Tavily API key |
| `GOOGLE_API_KEY` | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` |
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | `openai/gpt-oss-20b` |
| `LANGSMITH_API_KEY` | Optional LangSmith API key |
| `LANGSMITH_PROJECT` | `ScholarAI` |

Enter secret values directly in Render. Never commit them to
[`example.env`](./example.env) or GitHub.

#### Verify the deployment

After the first deploy, open the live service URL and check these endpoints:

```text
https://scholarai-amsd.onrender.com/health
https://scholarai-amsd.onrender.com/
https://scholarai-amsd.onrender.com/docs
```

The health endpoint should return:

```json
{"status":"ok"}
```

Then open the Vercel frontend and submit one small test profile. Watch
**Logs** in Render if the job fails. Provider errors usually mean a
missing/invalid environment variable or an exhausted provider quota.

The MCP server runs as a child process inside the web service, so the deployed
service must have project dependencies installed and start from the `app`
deployment root. The `pip install .` build command satisfies this requirement.

### Other suitable backend hosts

The application can also run on Railway, Fly.io, Google Cloud Run, Azure App
Service, or an Ubuntu VM with systemd and Nginx. Use this production command:

```bash
uvicorn api:app --host 0.0.0.0 --port "$PORT"
```

Do not use `--reload` in production.

### Frontend deployment: Vercel

Create a Vercel project using the `frontend` directory:

| Vercel field | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Set this environment variable in Vercel:

```text
VITE_API_BASE_URL=https://scholarai-amsd.onrender.com
```

The backend already allows `https://findscholarship.vercel.app` through CORS.

## Production considerations

Before treating the demo as a production service:

- Replace in-memory jobs with Redis, a database, or a managed task queue.
- Add authentication and rate limiting.
- Enforce upload size, file type, and request time limits.
- Store uploaded marksheets only temporarily and delete them after processing.
- Do not log uploaded document contents or API keys.
- Add domain validation and SSRF protections for user-supplied profile URLs.
- Add a persistent result store if users need to revisit workflows.
- Use a worker service for long-running jobs rather than a small in-process
  thread pool.
- Keep the allowed CORS origins limited to the deployed frontend and local
  development origins.
- Monitor provider quotas and LangSmith traces.

## Provider notes

- Gemini performs structured profile/evidence extraction and grounded drafting.
- Tavily performs discovery and page extraction. Page extraction is batched
  because the provider helper accepts at most 20 URLs per request.
- Groq reviews the generated shortlist but does not override deterministic
  eligibility auditing.
- MCP is local stdio communication between the workflow and provider-tool
  server. It is not a separately deployed network service in this design.
- LangSmith tracing is opt-in and activates only with
  `LANGSMITH_API_KEY`.

## Safety and result interpretation

ScholarAI is a research assistant, not an admissions authority. Always open the
official source link and verify deadlines, eligibility, funding, and required
documents before applying. A result marked `meets` means the available evidence
was compatible with the supplied profile; it is not a guarantee of admission
or funding.