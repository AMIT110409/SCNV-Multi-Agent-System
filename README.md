# SCNV Agent — Supply Chain Network Visibility Agent

![SCNV Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)
![React](https://img.shields.io/badge/react-18.x-61dafb.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)

An enterprise-grade, multi-agent AI framework designed to intelligently classify, route, and optimize Stock Transfer Orders (STOs) across a global supply chain network. The SCNV agent integrates deep predictive analytics, process mining, and graph-based relationships to prevent supply disruptions before they occur.

---

## 🌟 Key Features

- **Multi-Agent Orchestration (A2A)**: Utilizes LangGraph to coordinate between specialized AI agents (Analyst, Optimizer, Process Mining).
- **Interactive Network Visualization**: A rich, scalable React Flow dashboard that visualizes global Nodes (Plants & DCs) and Strategic Distribution Lanes.
- **Process Mining Integration**: Hooks into Celonis EMS to cross-verify LLM optimization decisions against real-time, compliance-based process execution data.
- **Hybrid Memory Layer**: Leverages Neo4j for topological network constraint retrieval and PostgreSQL (Supabase) for transactional memory.
- **NL-to-SQL Core**: Enables conversational querying of live SAP enterprise structural data via LangChain SQL Agent Toolkits.

---

## 🏛️ Architecture overview

The system is built on a 5-layer autonomous agent architecture:
1. **Perception**: REST endpoints ingesting JSON STO events and dashboard queries.
2. **Agent Core (A2A)**:
   - **SCM Analyst**: Triage and classification (Standard vs. Strategic).
   - **Optimizer**: Transportation algorithms calculating lead times, costs, and carbon footprints.
   - **Process Miner**: Celonis-driven compliance and bottleneck audits.
3. **Memory Layer**: Short-term execution state + Long-term graph context.
4. **Tools Interface**: Read/Write abilities into SAP ERP/WMS DB systems.
5. **Action Generation**: Autonomous JSON payloads containing validated logistical execution plans.

---

## 🛠️ Technology Stack

| Layer          | Technology                                   |
|----------------|----------------------------------------------|
| **Frontend**   | React.js, Vite, React Flow, TailwindCSS, Lucide Icons |
| **Backend**    | Python 3.10+, FastAPI, Uvicorn               |
| **AI / Logic** | LangChain, LangGraph, OpenAI (GPT-3.5/4)     |
| **Database**   | Supabase (PostgreSQL), Neo4j Graph Database  |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Node.js (v18+)
- Active Supabase instance
- OpenAI API Key

### 2. Backend Setup
Navigate to the backend directory and install dependencies:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r ../requirements.txt
```

Set up your `.env` file in the `backend/` directory:
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://postgres:...@...supabase.co:5432/postgres
SUPABASE_URL=https://....supabase.co
SUPABASE_ANON_KEY=...
```

Run the backend server:
```bash
uvicorn main:app --reload
```

### 3. Frontend Setup
Navigate to the frontend directory:
```bash
cd SCNV_Frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

---

## 📂 Project Structure

```text
scnv-agent/
├── agents/                  # LangGraph multi-agent logic (Analyst, Optimizer, etc.)
├── backend/                 # FastAPI REST application
│   ├── api/routes/          # Chat, Auth, and Network endpoints
│   ├── migrate_sap_data.py  # Supabase ingestion script
│   └── main.py              # Uvicorn entry point
├── data/                    # Synthetic SAP datasets (plants, dcs, stos)
├── SCNV_Frontend/           # React Web Client
│   ├── src/components/      # React Flow custom nodes (PlantNode, DCNode)
│   └── src/pages/           # Dashboards, Auth screens, Chat interface
└── docs/                    # Architecture diagrams and specifications
```

---

## 🔒 Security & Authentication
The application relies on Supabase Auth. All API endpoints targeting the backend (like `/api/network/map` and `/api/chat/`) require a valid JWT passed in the `Authorization: Bearer <token>` header. Waitlist, RLS (Row Level Security), and JWT verification hooks are fully configured.

---

## 🤝 Roadmap & Contribution
- [x] Phase 1-4: Agentic Framework, API, and DB build
- [x] Phase 5: Neo4j Graph Memory integration & Celonis Dashboard Toggles
- [ ] Phase 6: Shadow Mode enablement and Dockerization
- [ ] Phase 7: Prod Go-Live and live SAP integration
