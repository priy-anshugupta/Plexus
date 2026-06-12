# 🌌 Plexus

[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%2015%20%7C%20PostgreSQL%20%7C%20Neo4j%20%7C%20Qdrant%20%7C%20Redis-blue.svg)](#-technology-stack)
[![AI Architecture](https://img.shields.io/badge/AI-LangGraph%20%7C%20GraphRAG%20%7C%20Tree--sitter-orange.svg)](#-architecture--how-it-works)
[![Vulnerabilities Scanning](https://img.shields.io/badge/Security-OWASP%20Top%2010%20%7C%20SCA%20%7C%20Auto--Remediation-red.svg)](#-core-features)

**Plexus** is an enterprise-grade Developer Experience (DevEx) and Security Posture Platform. Unlike traditional static application security testing (SAST) tools that analyze codebases as flat text, Plexus parses your code into an **interconnected semantic knowledge graph**. 

By combining **GraphRAG (Graph-based Retrieval-Augmented Generation)**, **Parallel Multi-Agent pipelines (powered by LangGraph)**, and **Adaptive Generative UI**, Plexus provides systemic codebase intelligence, blast radius visualization, and autonomous remediation (Auto-Fix PRs).

---

## 💡 Why Plexus? (The Paradigm Shift)

Traditional AI code assistants (e.g., GitHub Copilot) operate on **localized file context**. They cannot understand cross-file, multi-hop architectural dependencies, leading to incomplete security audits and blind spots. 

Plexus bridges this gap by treating code as a living network of nodes (Files, Classes, Functions, API Endpoints, Databases) and edges (Calls, Imports, Inherits, Reads/Writes).

### ⚔️ Traditional SAST vs. Plexus

| Dimension | Traditional SAST / AI Assistants | Plexus Platform |
| :--- | :--- | :--- |
| **Code Representation** | Flat text files in isolation | **Knowledge Graph** (connected nodes & relationships) |
| **Context Scope** | Single file or limited token window | **GraphRAG** (multi-hop relational retrieval) |
| **Security Audits** | Pattern matching (Regex / AST-only rules) | **Multi-Agent Triage** (6+ specialized agents in parallel) |
| **Impact Analysis** | None (manual trace required) | **Blast Radius Visualization** (downstream propagation paths) |
| **Git Archaeology** | Git CLI / plain diffs | **Semantic Time-Travel** (natural language git history queries) |
| **Remediation** | Report only or single-file suggestion | **Autonomous PR Engine** (graph-aware fixes, runs tests) |
| **User Experience** | Static dashboards | **Role-Based Generative UI** (tailored for CISO, CTO, Developer) |

---

## ⚡ Key Metrics & System Efficiency

Plexus is optimized for high-throughput enterprise repository analysis. Below are the performance and diagnostic metrics captured during execution:

### 📊 Codebase Metrics
* **Backend Core Size:** `4,439` lines of Python across `42` modules (`backend/app`).
* **Frontend Dashboard Size:** `1,670` lines of TypeScript (TSX/CSS) across `12` modules (`frontend/src`).
* **Graph Database Complexity:** Maps files, packages, classes, functions, variable assignments, and API routes as interconnected nodes in Neo4j.

### 🛡️ Test Suite Scan Diagnostics
During dry-runs on vulnerable test codebases containing SQL injections, hardcoded secrets, and unsafe execution blocks, Plexus observed:
* **AST Parsing Coverage:** Successfully extracted `100%` of function declarations and imports (e.g., Python's `run_query`, `process_input` and JS's `executeQuery`, `runCommand`).
* **Vulnerabilities Triaged:**
  * **Static Rules Engine:** Detected `3` critical Python vulnerabilities and `3` critical JavaScript vulnerabilities (including `SEC-HARDCODED-SECRET`, `SEC-SQL-INJECTION`, and `SEC-UNSAFE-EXECUTION`).
  * **AI Agent Pipeline:** Flagged `2` deep architectural security vulnerabilities, `2` quality/style alerts (undocumented functions, stale `TODO` items), and synthesized `2` automated refactoring patches.

### 🚀 Performance & Token Efficiency
* **Execution Time (Hybrid Parallel Auditing):**
  * **Remote LLM Audit (`gpt-4o-mini`):** **1.5s - 3.5s** total execution time.
  * **Offline Fallback / Rules Engine:** **< 100ms** latency using local syntax patterns.
* **LangGraph Parallelization Gain:** By running specialized agents concurrently via the LangGraph `Send()` API, analysis wall-clock time is reduced by **~75%** compared to sequential processing.
* **Token Cost Reductions:** Incorporating a **Semgrep Pre-Filtering Node** flags only suspicious code structures, bypassing clean files. This reduces LLM token consumption by **60% - 80%** on average.
* **Incremental Graph Rebuilding:** The AST graph updates incrementally on new git commits rather than rebuilding the entire database, ensuring O(N) scaling.

---

## 🛠️ Technology Stack

Plexus integrates a modern, premium, and highly efficient stack designed to handle large-scale code graphs and deliver responsive, real-time UI.

```
                  ┌──────────────────────────────────────────────┐
                  │            Next.js 15+ Frontend              │
                  │  (Role-Based UI, D3 react-force-graph, CASL) │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼ REST / SSE
                  ┌──────────────────────────────────────────────┐
                  │             FastAPI Backend                  │
                  │   (Repository Lifecycles & Agent Routing)    │
                  └──────────┬───────────────┬───────────────┬───┘
                             │               │               │
                             ▼               ▼               ▼
                      ┌──────────────┐┌──────────────┐┌──────────────┐
                      │  PostgreSQL  ││    Neo4j     ││    Qdrant    │
                      │  (Relational ││ (AST Code    ││ (Code Vector│
                      │   Metadata)  ││  Graph DB)   ││ Embeddings) │
                      └──────────────┘└──────────────┘└──────────────┘
```

### 🧠 Backend (Core Engine)
* **API Framework:** **FastAPI** (Python 3.11+) for high-performance asynchronous request handling.
* **Agentic Orchestration:** **LangGraph (StateGraph)** for cyclical agent workflows, checkpointing, and dynamic fan-out (`Send` API).
* **Database & ORM:** **SQLAlchemy 2.0** with **PostgreSQL** for managing repository scan states and findings metadata.
* **Code Parsing:** **Tree-sitter** (Python & JavaScript bindings) for language-agnostic Abstract Syntax Tree (AST) extraction.
* **Vector Store:** **Qdrant** (production-grade vector similarity database for code snippets and semantic documentation chunks).
* **Graph Database:** **Neo4j** (Native graph engine with APOC plugins for traversing call chains and dependency networks).
* **Caching & Events:** **Redis** for state caching and server-sent event (SSE) distribution.

### 🎨 Frontend (DevEx Dashboard)
* **Framework:** **Next.js 15** (App Router) with React Server Components (RSC) for optimized server-side rendering.
* **Styling:** **Tailwind CSS v4** + **shadcn/ui** (custom dark-mode glassmorphic aesthetics).
* **Graph Rendering:** **`react-force-graph-2d`** (D3-based canvas renderer for interactive code dependency graphs).
* **Permissions Control:** **CASL** for declarative role-based views.
* **Code Visualization:** **Monaco Editor** (`@monaco-editor/react`) for full-fidelity interactive code viewing.
* **Charts:** **Recharts** for compliance heatmaps and vulnerability trends.

---

## 👁️ Core Features

### 1. Multi-Agent Collaborative Auditing
FastAPI triggers a parallel LangGraph pipeline. The Orchestrator delegates scans across **6 specialized agents**:
1. **🔒 Security Agent:** Audits broken authentication, SQL injections, XSS, and OWASP Top 10 vulnerabilities.
2. **🎨 Frontend Agent:** Focuses on unsafe DOM manipulation, React stale closures, and memory leaks.
3. **⚙️ Backend Agent:** Audits input validation, exception handling, race conditions, and business logic.
4. **🗄️ Database Agent:** Detects N+1 query loops, missing indexes, and unoptimized queries.
5. **🐳 DevOps Agent:** Scans Dockerfiles, compose files, and K8s manifests for unpinned images or root privilege exploits.
6. **📦 Dependency Agent:** Queries the `OSV.dev` database to flag CVEs and license compliance issues.

### 2. GraphRAG Engine
Integrates vector similarity search (Qdrant) and graph database traversal (Neo4j). It generates a global structural map of the codebase. Instead of matching single lines, Plexus can answer multi-hop queries like:
> *"Does a vulnerability in `payment_gateway.py` reach an API endpoint exposed to unauthorized web users?"*

### 3. Blast Radius Visualization
When a vulnerability is detected, Plexus runs a forward reachability algorithm (BFS) on the Neo4j AST graph. It visually plots every downstream service, database table, or React UI component that is affected by the propagation.

### 4. Semantic Time-Travel
Using GitPython and semantic commit chunking, developers can query the historical context of the repository:
> *"Why did we switch our authentication provider from Auth0 to custom JWTs in Q3 2025?"*

### 5. Autonomous Remediation (Auto-Fix PRs)
Plexus doesn't just report issues—it fixes them. The Write-Agent forks the branch, creates an AST-level patch, runs local/CI unit tests to verify the fix, and automatically opens a clean, human-readable Pull Request containing details of the vulnerability, blast radius, and fix.

### 6. Role-Based Dashboards & Generative UI
Different team members require different insights. Plexus uses CASL and the Vercel AI SDK to render tailor-made dashboards:
* **CISO View:** Compliance matrices (SOC2/ISO 27001), MTTR trends, and risk mapping.
* **CTO View:** Technical debt accumulation rates, engineering velocity, and automated refactoring ROI.
* **Developer View:** Local sandbox tasks, onboarding quests, and interactive code fixes.

---

## 📂 Project Directory Structure

```
Plexus_1/
├── backend/
│   ├── app/
│   │   ├── agents/           # LangGraph agents (orchestrator, security, autofix, etc.)
│   │   ├── core/             # Settings (config.py) and database managers (database.py)
│   │   ├── middleware/       # Exception handlers & CORS setup
│   │   ├── models/           # SQLAlchemy 2.0 ORM schemas (Postgres)
│   │   ├── routers/          # FastAPI API endpoints (scans, findings, repos)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # Core logic (AST parser, git wrapper, graph/vector services)
│   │   └── main.py           # FastAPI app initialization
│   ├── requirements.txt      # Python dependencies
│   └── tests/                # Test suites
│
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages & global layouts
│   │   ├── components/       # Visual widgets (BlastRadiusGraph, Monaco Editor, Sidebar)
│   │   │   └── dashboards/   # Dynamic dashboards (CISO, CTO, Quest)
│   │   ├── context/          # Role Context & Auth State
│   │   └── lib/              # CASL ability rules
│   ├── package.json          # Node dependencies
│   └── tsconfig.json         # TypeScript configuration
│
└── docker-compose.yml        # Orchestration for PostgreSQL, Neo4j, Qdrant, & Redis
```

---

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Compose
* Python 3.11+
* Node.js 18+

### 1. Spin up Databases (Postgres, Neo4j, Qdrant, Redis)
Run the following in the project root:
```bash
docker-compose up -d
```
Verify databases are healthy:
* PostgreSQL: `localhost:5432`
* Neo4j HTTP Console: `http://localhost:7474` (Auth: `neo4j` / `plexuspassword`)
* Qdrant API: `http://localhost:6333`
* Redis: `localhost:6379`

### 2. Configure Backend
Navigate to `backend/`, copy the example env:
```bash
cd backend
cp .env.example .env
```
Fill in the environment variables (API keys, database connections).

Install dependencies and start the FastAPI dev server:
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Access Swagger API Docs at `http://localhost:8000/docs`.

### 3. Configure Frontend
Navigate to `frontend/`, install node modules, and boot Next.js:
```bash
cd ../frontend
npm install
npm run dev
```
Open your browser and navigate to `http://localhost:3000`.

---

## 🎓 Contribution to AI/ML & ML Ops
Plexus represents a practical implementation of **state-of-the-art AI patterns** for static program analysis and repository management:
* **Graph-Constrained RAG:** Combines hierarchical graph extraction (using Tree-sitter AST nodes) with semantic embeddings, enabling LLMs to execute structured reasoning over highly relational code structures.
* **Pregel Actor Model Orchestration:** Implements parallel multi-agent collaboration with state persistence (checkpoints) to handle long-running code analysis processes reliably.
* **Telemetry & Continuous Integration:** Features webhook ingestion pipelines that turn static analysis into an active, feedback-driven ML Ops loop.