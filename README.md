# 🏭 FactoryOS

> **Production-grade Multi-Agent Manufacturing Operations Platform**  
> Built for the Google AI Agents Intensive Capstone — Agents for Business track.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini_2.0-blue)](https://ai.google.dev/)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## What is FactoryOS?

FactoryOS is a **Multi-Agent AI platform** that helps Plant Managers respond to manufacturing disruptions. When a machine fails, inventory runs short, or a production deadline is at risk, FactoryOS:

1. **Classifies** the incident via a Manager Agent
2. **Analyzes** it in parallel across 5 specialist AI agents
3. **Generates** 3 recovery plans (Economical, Rapid, Balanced)
4. **Presents** plans for human review and approval

The manufacturing domain is the **business scenario**. The real demonstration is the AI engineering:

- Multi-Agent Orchestration with `asyncio.gather()` for parallel execution
- Google Gemini 2.0 integration with schema-constrained JSON output
- Model Context Protocol (MCP) tool layer (7 tools)
- Skills layer for deterministic pre-processing (5 skills)
- Human-in-the-loop approval workflow
- Production-grade FastAPI + Next.js architecture

---

## Architecture

```
Plant Manager
     │
     ▼
 Incidents Page ──── POST /api/v1/analysis/incidents
     │
     ▼
Manager Agent (Orchestrator)
     │
     ├── asyncio.gather() ──────────────────────────────┐
     │                                                  │
     ├─► Maintenance Agent     ├─► MCP Tools            │
     │   (machine history,     │   machine_history       │
     │    maintenance logs)    │   maintenance_logs      │
     │                         │   inventory_lookup      │
     ├─► Inventory Agent       │   supplier_lookup       │
     │   (stock, suppliers)    │   production_schedule   │
     │                         │   cost_estimator        │
     ├─► Production Agent      │   incident_history      │
     │   (schedule, deadlines) │                         │
     │                         └─────────────────────────┘
     ├─► Cost Intelligence Agent
     │   (financial models)
     │
     ▼
Manager Agent (Synthesis)
     │
     ├─► Plan A — Economical
     ├─► Plan B — Rapid
     └─► Plan C — Balanced
           │
           ▼
    Reporting Agent
    (Executive Summary)
           │
           ▼
    Decision Center
    (Human Approval)
```

---

## Google ADK Alignment

FactoryOS is architected to align with Google ADK principles:

| ADK Concept | FactoryOS Implementation |
|-------------|--------------------------|
| `Agent` class | `BaseAgent` abstract class |
| `agent.run()` | `agent.execute(context)` |
| `Agent(tools=[...])` | `MCPToolRegistry` |
| Parallel agents | `asyncio.gather()` in `ManagerAgent` |
| Tool protocol | MCP `BaseMCPTool` with `run()` interface |
| Schema output | Pydantic `response_schema` in Gemini config |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 + React 19 + Material UI 6 |
| Backend | FastAPI 0.115 + Python 3.11 |
| AI | Google Gemini 2.0 Flash |
| Tool Protocol | MCP (Model Context Protocol) |
| Validation | Pydantic 2.10 (schema-constrained output) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Deployment | Docker Compose |

---

## Project Structure

```
FactoryOS/
├── backend/                    FastAPI backend
│   ├── app/
│   │   ├── agents/             AI agents
│   │   │   ├── orchestrator/   Manager Agent (orchestrator)
│   │   │   ├── maintenance/    Maintenance Agent
│   │   │   ├── inventory/      Inventory Agent
│   │   │   ├── production/     Production Agent
│   │   │   ├── cost/           Cost Intelligence Agent
│   │   │   └── reporting/      Reporting Agent
│   │   ├── api/v1/             REST endpoints
│   │   │   ├── analysis.py     AI Platform endpoints
│   │   │   ├── health.py       Health checks
│   │   │   └── incidents.py    Incident CRUD
│   │   ├── core/               Config, Gemini client, logging
│   │   ├── mcp/                MCP tool registry (7 tools)
│   │   ├── schemas/            Pydantic schemas
│   │   ├── services/           AI Platform composition root
│   │   └── skills/             Deterministic pre-processing (5 skills)
│   ├── tests/                  Integration test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   Next.js frontend
│   └── src/
│       ├── app/                App Router pages
│       │   ├── dashboard/      Manufacturing overview
│       │   ├── incidents/      Incident submission form
│       │   ├── decisions/      Decision Center (Plan A/B/C)
│       │   └── reports/        Analysis reports
│       ├── components/         Reusable UI components
│       ├── lib/                API client + sessionStorage store
│       ├── theme/              Material Design 3 theme
│       └── types/              TypeScript contracts
│
├── datasets/                   Evaluation scenarios
├── docs/                       Documentation
├── deployment/                 Deployment guides
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Prerequisites

- Python 3.11
- Node.js 20+
- Git

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/FactoryOS.git
cd FactoryOS
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (Python 3.11 required)
py -3.11 -m venv venv

# Activate (Windows)
venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env and set GEMINI_API_KEY (optional — runs in MOCK MODE without it)

# Start backend
uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/api/docs**

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:3000**

### 4. Run with Docker

```bash
# From the root directory
cp .env.example .env
# Set GEMINI_API_KEY in .env

docker-compose up --build
```

---

## AI Platform Demo

### Option A: Web UI (Recommended)

1. Open **http://localhost:3000**
2. Navigate to **Incidents** in the sidebar
3. Click **"Run Demo Analysis"** (no form needed)
4. Watch the multi-agent pipeline execute
5. Review **Plan A, B, C** in the Decision Center
6. Approve a plan

### Option B: API Direct

```bash
# Health check
curl http://localhost:8000/api/v1/health

# AI Platform status
curl http://localhost:8000/api/v1/analysis/status

# Run demo analysis (Machine M-12 bearing failure)
curl http://localhost:8000/api/v1/analysis/incidents/demo

# Submit a custom incident
curl -X POST http://localhost:8000/api/v1/analysis/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "incident": {
      "title": "Pump P-07 Failure",
      "description": "Coolant pump P-07 has seized. Line B overheating.",
      "equipment_id": "P-07",
      "severity": "high"
    }
  }'
```

### Option C: Interactive Docs

Open **http://localhost:8000/api/docs** — all endpoints are documented with examples.

---

## Running Tests

```bash
cd backend

# Install test dependencies (into activated venv)
pip install pytest pytest-asyncio httpx

# Run all tests (MOCK mode — no API key needed)
pytest tests/ -v
```

Expected output: **~25 tests passing** covering:
- Health & version endpoints
- Platform status (5 agents, 7 tools)
- Demo analysis (3 plans, schema validation)
- Custom incident analysis
- Input validation (422 errors)

---

## Gemini API Key

Without a key, FactoryOS runs in **MOCK MODE**:
- All endpoints work normally
- Agent responses are realistic simulated data
- The full UI workflow is functional
- Responses clearly label `"gemini_mode": "mock"`

With a key, the agents use **Gemini 2.0 Flash** for real AI analysis.

Obtain a key: https://aistudio.google.com/app/apikey

---

## Key Design Decisions

**Why `asyncio.gather()` instead of sequential agent calls?**  
Four domain agents run simultaneously, reducing total latency from ~4× per-agent time to ~1× (the slowest agent). This mirrors ADK's parallel execution model.

**Why MCP tool layer?**  
The MCP interface decouples agents from data sources. Agents call `tool.run(input)` without knowing implementation details. Swap mock tools for real IoT/ERP integrations without touching agent code.

**Why sessionStorage for frontend state?**  
No authentication sprint was in scope. sessionStorage provides secure, tab-scoped persistence that clears when the session ends — appropriate for sensitive manufacturing decisions.

**Why SQLite + SQLAlchemy abstraction?**  
Zero infrastructure for development. The async driver swap (`aiosqlite` → `asyncpg`) plus a URL change is the only migration needed for PostgreSQL. No ORM code changes required.

---

## Roadmap

### Completed
- ✅ Multi-Agent orchestration (Manager + 5 domain agents)
- ✅ Gemini 2.0 Flash integration with schema-constrained output
- ✅ MCP tool layer (7 tools)
- ✅ Skills layer (5 skills)
- ✅ Human-in-the-loop approval workflow
- ✅ Material Design 3 dashboard
- ✅ Incident submission with animated AI pipeline visualization
- ✅ Decision Center (Plan A/B/C with approve/reject/review)
- ✅ Executive reports
- ✅ Integration test suite
- ✅ Docker deployment

### Future
- 🔲 Google ADK migration (wrap BaseAgent with `google.adk.agents.Agent`)
- 🔲 IoT sensor integration
- 🔲 PostgreSQL + Alembic migrations
- 🔲 Authentication (JWT/OAuth)
- 🔲 Real-time updates (WebSocket)
- 🔲 Mobile app

---

## License

MIT © 2026 FactoryOS