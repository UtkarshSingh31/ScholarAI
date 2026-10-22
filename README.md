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

The application is intentionally conservative: missing or incomparable evidence
is reported as `unknown`, not as proof of eligibility.

## Current architecture

The project is a Python/FastAPI application. The dashboard is a static HTML
page served by the same FastAPI process, so a separate frontend server or
frontend build step is not required.

```text
Browser
  |
  | GET / and multipart form submission
  v
FastAPI (app/api.py)
  |
  v
LangGraph workflow
  |-- Gemini: profile extraction, evidence extraction, application draft
  |-- Tavily: web search and page extraction
  |-- local MCP server: provider tools over stdio
  |-- Groq: shortlist review
  |-- LangSmith: optional tracing
  v
Dashboard results
```

Important directories:

```text
app/
  agents/          Workflow agent implementations
  static/          Browser dashboard
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

Using `uv`:

```powershell
uv sync
```

Using pip:

```powershell
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

### 4. Start the application

PowerShell:

```powershell
python -m uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Open the dashboard at <http://127.0.0.1:8000/>.

The interactive API documentation is at <http://127.0.0.1:8000/docs> and the
health check is at <http://127.0.0.1:8000/health>.

The local MCP server is started automatically by the workflow when the Hunter
or Evidence agent calls an MCP tool. Do not start `app/mcp_server.py`
separately for normal application use.

## Using the dashboard

1. Open `http://127.0.0.1:8000/`.
2. Enter a profile as JSON, for example:

   ```json
   {
     "name": "Rahul",
     "degree": "B.Tech CSE",
     "cgpa": 8.2,
     "cgpa_scale": "10",
     "preferred_countries": ["Canada", "Germany", "Singapore"],
     "budget": "low"
   }
   ```

3. Add public profile URLs one per line, such as a GitHub profile.
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

### Recommended first deployment: Render

Render is a straightforward option because it can run one Python web service
and provides environment-variable management.

Create a **Web Service** connected to this repository with:

- **Runtime:** Python
- **Build command:**

  ```text
  pip install .
  ```

- **Start command:**

  ```text
  uvicorn app.api:app --host 0.0.0.0 --port $PORT
  ```

- **Health check path:** `/health`

Add these environment variables in the Render dashboard:

```text
TAVILY_API_KEY
GOOGLE_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GROQ_API_KEY
GROQ_MODEL=openai/gpt-oss-20b
LANGSMITH_API_KEY       # optional
LANGSMITH_PROJECT=ScholarAI
```

Render provides one URL for both the dashboard and API:

```text
https://your-service.onrender.com/
https://your-service.onrender.com/docs
https://your-service.onrender.com/health
```

The MCP server runs as a child process inside the web service, so the deployed
service must have project dependencies installed and start from the repository
root. The `pip install .` build command satisfies this requirement.

### Other suitable backend hosts

The application can also run on Railway, Fly.io, Google Cloud Run, Azure App
Service, or an Ubuntu VM with systemd and Nginx. Use this production command:

```bash
uvicorn app.api:app --host 0.0.0.0 --port "$PORT"
```

Do not use `--reload` in production.

### Frontend deployment options

The current frontend is already served by FastAPI. The simplest production
setup is one backend service and one public URL.

If a separate frontend is desired later, move `app/static/index.html` into a
dedicated frontend project, configure its API base URL, and add CORS to the
FastAPI service. That is not necessary for the current application.

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
- Configure CORS only if a separate frontend is introduced.
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