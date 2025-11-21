# 🧠 NLP Query Engine for Employee Data

A full-stack AI-powered application that lets you query your employee database using **natural language** no SQL knowledge required.  
It dynamically adapts to your database schema and can fetch answers from uploaded documents (resumes, PDFs, etc.).

---

## 🚀 Core Features

- **Dynamic Schema Discovery** – Auto-detects tables, columns, and relationships from a connected DB.  
- **Natural Language Queries** – Convert plain-English questions into SQL or semantic searches using an LLM.  
- **Hybrid Search** – Combine results from structured (SQL) and unstructured (documents) sources.  
- **Document Ingestion** – Upload PDF, DOCX, TXT, CSV → create embeddings → store in FAISS.  
- **Performance Optimized** – Async processing, caching, connection pooling, FAISS vector search.

---

## 🧰 Tech Stack

- **Backend** – FastAPI (Python)  
- **Frontend** – React (Vite)  
- **Database** – PostgreSQL  
- **LLM Integration** – Groq (or other LLM provider) for NL → SQL translation  
- **Embeddings** – Sentence-Transformers  
- **Vector Store** – FAISS  
- **Cache** – Redis

---

## 📁 Folder Structure

```text
nlp-query-engine/
├── backend/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── uploads/
│   ├── venv/
│   ├── main.py
│   ├── .env
│   ├── requirements.txt
│   ├── requirements-simple.txt
│   ├── requirements-minimal.txt
│   └── test.db
├── frontend/
│   ├── node_modules/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── README.md
├── sample_offer_letter.txt
└── sample_resume.txt
```

> Note: `main.py` lives in `backend/` (root of backend). Start commands reference that location.

---

## ⚙️ Getting Started (Local Setup)

### 🧩 Prerequisites

- Python 3.8+  
- Node.js 18+ (npm)  
- PostgreSQL (local or remote)  
- Redis (optional — recommended for caching)  
- A Groq API key (or other LLM provider key)

---

### 🪄 Setup Steps

#### 1) Clone the repository
```bash
git clone <your-repo-url>
cd nlp-query-engine
```

#### 2) Create env file (backend/.env)
Create `backend/.env` with at least the following variables:
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nlp_query_engine
REDIS_URL=redis://localhost:6379

CACHE_TTL=3600
MAX_FILE_SIZE=10485760
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
MAX_RESULTS=100

ALLOWED_ORIGINS=http://localhost:5173
```

Adjust values for your environment (DB host, ports, credentials).

---

### 🧠 Run the Backend (manual commands)

1. Create & activate a Python virtual environment (recommended):

**macOS / Linux**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```
- If you want a lighter set for development/testing use `requirements-simple.txt` or `requirements-minimal.txt`.

3. Start the FastAPI server:

**Option A — run with uvicorn (common):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option B — run with python (if `main.py` contains `uvicorn.run(...)`):**
```bash
python main.py
```

By default the backend will be available at `http://localhost:8000`. API docs: `http://localhost:8000/docs`.

---

### 💻 Run the Frontend (manual commands)

Open a new terminal tab/window:

```bash
cd frontend
npm install
npm run dev
```

Default Vite URL: `http://localhost:5173` (or the URL printed in the terminal).

---

### 🌐 Access the App
- **Frontend UI:** `http://localhost:5173`  
- **Backend (API):** `http://localhost:8000`  
- **Backend API Docs (Swagger):** `http://localhost:8000/docs`

---

## 🧩 Example User Queries

**SQL-style questions**
- “Show me all employees in the Engineering department.”  
- “What's the average salary by department?”  
- “List employees hired in the last 6 months.”

**Document-style questions**
- “Find resumes mentioning Python and AWS.”  
- “Search performance reviews for 'leadership'.”

**Hybrid queries**
- “Show engineers with Python skills and include salary data.”
- “Find resumes with ML experience and match with DB employee records.”

---

## 🧱 API Endpoints (Overview)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/connect-database` | Connect to DB and discover schema |
| POST | `/api/upload-documents` | Upload and process documents |
| GET | `/api/documents` | List uploaded documents |
| DELETE | `/api/documents/{filename}` | Delete a document |
| POST | `/api/query` | Run a natural language query |
| GET | `/api/query/history` | Get query history |
| DELETE | `/api/query/cache` | Clear query cache |
| GET | `/health` | Health check |

> Exact paths may vary depending on your `backend/api` routes. Confirm routes in `backend/api/` if you modified them.

---

## 🧩 Development Notes

- Use `requirements-minimal.txt` for the smallest dependency set during quick tests; use `requirements.txt` for full features (embeddings, FAISS, etc.).  
- If you use Docker, `docker-compose.yml` (if present) can orchestrate `postgres`, `redis`, `backend`, and `frontend`. This README focuses on manual local setup.  
- Make sure the `DATABASE_URL` points to a running PostgreSQL instance and that the DB exists (create DB `nlp_query_engine` if needed).

---

## 🤝 Contributing

1. Fork the repo  
2. Create a branch: `git checkout -b feature/your-feature`  
3. Commit your changes and push  
4. Open a pull request describing your change

Please add tests for new features when possible.

---

## 📄 License

I don’t believe in locking down ideas or restricting usage.  
If your idea can be copied and executed better — that’s not theft, that’s talent.  

So go ahead, use it, learn from it, build something better.  
Because real moat isn’t secrecy — it’s **skill, speed, and consistency**.  

---

## 🆘 Support

If you need help:
- Open an issue in this repository with logs and a short description of the problem.  
- Include backend logs (terminal output) and any errors from the browser console for frontend issues.

---
