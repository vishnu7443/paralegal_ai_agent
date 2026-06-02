# Paralegal Agentic Auditor ⚖️🤖

An explainable, deterministic, multi-agent AI operations manager designed for small businesses to audit legal contracts, assess risk, and perform real-time semantic analysis.

This project implements a **Think → Decide → Act → Observe → Repeat** autonomous reasoning cycle using a modular multi-agent structure built with LangGraph, FAISS, and Google Gemini API.

---

## 🏗️ Architecture & Agent Responsibilities

The auditor is built around **modular agents with shared memory** that run inside a structured workflow state:

1. **Upload / Ingestion Pipeline:** Splits PDFs into semantic blocks, embeds them, and saves the vectors locally into a FAISS index.
2. **Clause Agent (Extractor):** Scans the document, matches clauses against a legal risk lexicon (indemnification, liability, termination, intellectual property, governing law), and categorizes them.
3. **Risk Agent (Profiler):** Scores each extracted clause (1-10 scale) based on severity, liability exposure, and asymmetry, providing explicit reasoning and recommended actions.
4. **Report Agent (Synthesizer):** Orchestrates findings into a premium, executive-grade legal brief using the Google Gemini API, or falls back to a deterministic local template generator.
5. **Orchestrator Graph (LangGraph):** Links all agents together into an autonomous, state-driven workflow that streams real-time logs and report tokens to the client.

```
                    ┌────────────────────────┐
                    │  Upload & PDF Ingest   │
                    └───────────┬────────────┘
                                │ (FAISS Indexing)
                                ▼
                    ┌────────────────────────┐
                    │   Clause Agent (Think) │
                    └───────────┬────────────┘
                                │ (Extracts Lexicon risks)
                                ▼
                    ┌────────────────────────┐
                    │   Risk Agent (Decide)  │
                    └───────────┬────────────┘
                                │ (Assess & profile)
                                ▼
                    ┌────────────────────────┐
                    │   Report Agent (Act)   │
                    └───────────┬────────────┘
                                │ (Stream report tokens)
                                ▼
                    ┌────────────────────────┐
                    │  Complete (Observe)    │
                    └────────────────────────┘
```

---

## 🛠️ Technology Stack

* **Frontend:** Next.js (React 19, TypeScript, TailwindCSS, Lucide Icons, canvas-confetti).
* **Backend:** FastAPI (Python 3.12, Uvicorn, SQLAlchemy, LangGraph, FAISS, ReportLab).
* **Database:** SQLite (local fallback `paralegal_analysis.db`) or PostgreSQL.
* **LLM Engine:** Google Gemini API (`models/text-embedding-004` and `gemini-1.5-flash`).

---

## ⚡ Quick Start & Local Setup

### Prerequisites
* Python 3.12+
* Node.js 20+

### 1. Backend Setup

1. Navigate to the root directory and create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # On Windows
   source .venv/bin/activate    # On Unix/macOS
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Configure environment variables in a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@localhost:5432/paralegal_analysis  # Optional
   ```

4. Start the FastAPI development server:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
   The backend will be available at `http://localhost:8000`. You can inspect endpoints via `http://localhost:8000/docs`.

### 2. Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install npm packages:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## 🚀 Vercel Deployment

This repository is configured as a multi-service project in Vercel using `vercel.json` at the root directory:

```json
{
  "experimentalServices": {
    "frontend": {
      "root": "frontend",
      "routePrefix": "/",
      "framework": "nextjs"
    },
    "backend": {
      "root": "backend",
      "entrypoint": "main.py",
      "routePrefix": "/_/backend"
    }
  }
}
```

### Deployment Configuration Steps:
1. Push your repository to GitHub.
2. Create a new project on Vercel and import this repository.
3. Under the **Environment Variables** tab in your Vercel project, add:
   * `GEMINI_API_KEY`: Your Google Gemini API Key.
   * `DATABASE_URL` (Optional): A hosted PostgreSQL connection string (e.g. Neon, Supabase).
4. Click **Deploy**. Vercel will automatically split the project into Next.js edge routes (`/`) and a serverless Python FastAPI backend (`/_/backend`).

---

## 🧪 Running Validation Tests

You can run automated tests to check the RAG parsing, indexing, and agent orchestration flows locally:

* **Verify RAG pipeline (Extraction & FAISS store):**
  ```bash
  .venv\Scripts\python backend/scratch/test_rag.py
  ```
* **Verify Multi-agent LangGraph orchestrator:**
  ```bash
  .venv\Scripts\python backend/scratch/test_orchestrator.py
  ```
* **Verify API document uploading & analysis ingestion:**
  ```bash
  .venv\Scripts\python backend/scratch/test_api_ingest.py
  ```

---

## ⚖️ Disclaimer

*This application is for demonstration and evaluation purposes only. It does not constitute formal legal advice. Always consult with a qualified attorney for official contract negotiations and reviews.*
