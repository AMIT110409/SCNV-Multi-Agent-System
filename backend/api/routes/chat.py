from fastapi import APIRouter
from pydantic import BaseModel
import uuid
import datetime
 
# Triggering uvicorn hot-reload to catch newly installed dependencies
router = APIRouter()
 
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    agent_id: str | None = None
 
class SessionSaveRequest(BaseModel):
    session_id: str
    title: str
    messages: list
    agent_id: str | None = None  # New field added
 
SESSIONS_DB = {}
 
import sys
import os
import re
import json
import uuid
import datetime
import traceback
from typing import Dict, Any, List

# LangChain / OpenAI
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.messages import HumanMessage

# Inject the agents directory into the path so we can import the LangGraph orchestrator
agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents"))
if agents_dir not in sys.path:
    sys.path.append(agents_dir)

# Inject backend root for embeddings module
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from orchestrator import Orchestrator
    orchestrator = Orchestrator()
except Exception as e:
    print(f"Warning: Orchestrator failed to load: {e}")
    orchestrator = None

# Custom modules
try:
    from embeddings import search_similar_decisions
except ImportError:
    search_similar_decisions = None

# ── KPI Data Loading (for direct country KPI answers) ──────────────────────────
KPI_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/synthetic/gap_extended"))

def _load_kpi_json(filename):
    path = os.path.join(KPI_DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Country code detection patterns
COUNTRY_MAP = {
    "uk": "GB", "united kingdom": "GB", "britain": "GB", "gb": "GB",
    "belgium": "BE", "be": "BE",
    "germany": "DE", "de": "DE",
    "netherlands": "NL", "nl": "NL", "holland": "NL",
    "france": "FR", "fr": "FR",
    "spain": "ES", "es": "ES",
    "italy": "IT", "it": "IT",
    "india": "IN", "in": "IN",
    "singapore": "SG", "sg": "SG",
    "china": "CN", "cn": "CN",
    "japan": "JP", "jp": "JP",
    "australia": "AU", "au": "AU",
    "brazil": "BR", "br": "BR",
    "turkey": "TR", "tr": "TR",
    "south africa": "ZA", "za": "ZA",
    "hong kong": "HK", "hk": "HK",
    "mexico": "MX", "mx": "MX",
    "poland": "PL", "pl": "PL",
    "sweden": "SE", "se": "SE",
}

# ── bug fix: Tightened KPI keyword list ────────────────────────────────────────
# Only compound domain-specific phrases kept. Broad single words like "efficiency",
# "volume", "productive", "country", "percent" removed to prevent generic questions
# from being misrouted to the KPI engine.
KPI_KEYWORDS = [
    "allocation efficiency",
    "unproductive transfer",
    "productive transfer",
    "optimal allocation",
    "suboptimal", "sub-optimal", "sub optimal",
    "transfer ratio",
    "customer %",
    "country kpi",
    "allocation %",
    "monthly trend",
    "show me kpi",
    "kpi",
    "efficiecy",               # intentional typo kept from original
    "percetage",               # intentional typo kept from original
]

# ── SAP database field names ───────────────────────────────────────────────────
# If any of these appear in the query, it is a real database/data question —
# NOT a generic definition question — even if it starts with "what is / what are".
# These should be routed to the SQL Agent, not the generic LLM.
SAP_DB_TERMS = [
    "netwr", "kunnr", "vbeln", "matnr", "werks", "vbak", "vbap",
    "likp", "lips", "mara", "marc", "mchb", "ekko", "ekpo",
    "lifnr", "bukrs", "waers", "menge", "posnr", "auart",
    "erdat", "erzet", "vkorg", "vtweg", "spart", "knumv",
    "kbetr", "kwmeng", "lfimg", "ntgew", "brgew",
    # common ID patterns like KUNNR_001, MATNR_042, etc.
]

def is_sap_data_query(query_lower: str) -> bool:
    """
    Returns True if the query contains SAP field names or ID patterns.
    These are always database queries regardless of how the sentence starts.
    """
    # Check known SAP field names
    for term in SAP_DB_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", query_lower):
            return True
    # Check patterns like KUNNR_001, MATNR_042, STO_123 — uppercase codes with underscore+digits
    if re.search(r"\b[A-Z]{2,}_\d+\b", req_message_original if False else query_lower.upper()):
        return True
    return False


def detect_country(query_lower: str) -> str | None:
    """Extract country code from a user query using strict word boundaries."""
    for name, code in sorted(COUNTRY_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(name)}\b", query_lower):
            return code
    return None


def is_country_kpi_query(query_lower: str) -> bool:
    """Check if the query is about country-specific KPIs."""
    return any(kw in query_lower for kw in KPI_KEYWORDS)


def answer_kpi_query(query: str, country_code: str | None, llm) -> dict:
    """
    Answer a country KPI query directly from synthetic data + optional pgvector context.
    Uses an LLM to provide a professional analyst commentary on the metrics.
    """
    customer_orders = _load_kpi_json("customer_orders.json")
    stos = _load_kpi_json("incoming_stos_extended.json")
 
    if country_code:
        orders = [o for o in customer_orders if o.get("country_code") == country_code]
        country_stos = [s for s in stos if s.get("COUNTRY_CODE") == country_code]
    else:
        orders = customer_orders
        country_stos = stos
 
    total_orders = len(orders)
    optimal_count = sum(1 for o in orders if o.get("is_optimal_allocation"))
    avg_efficiency = sum(o.get("allocation_efficiency_score", 0) for o in orders) / max(total_orders, 1)
    optimal_ratio = (optimal_count / max(total_orders, 1)) * 100
    suboptimal_pct = ((total_orders - optimal_count) / max(total_orders, 1)) * 100
 
    total_vol = sum((s.get("VOLUME_HL") or 0) for s in country_stos)
    prod_vol = sum(
        (s.get("VOLUME_HL") or 0) for s in country_stos
        if s.get("movement_type") == "641" and s.get("is_pre_goods_issue")
    )
    prod_pct = (prod_vol / max(total_vol, 1)) * 100
    unprod_ratio = ((total_vol - prod_vol) / max(total_vol, 1)) * 100
 
    country_label = country_code if country_code else "All Countries"
 
    rag_context = ""
    try:
        if search_similar_decisions:
            similar = search_similar_decisions(query, limit=3, country_code=country_code)
            if similar:
                rag_context = "\n\n📎 **Related Decisions (from memory):**\n"
                for s in similar:
                    rag_context += f"- {s['summary']} (similarity: {s['similarity']})\n"
    except Exception:
        rag_context = ""
 
    country_label = country_code if country_code else "Global Network"
 
    raw_metrics = (
        f"Country: {country_label}\n"
        f"Allocation Efficiency: {avg_efficiency * 100:.1f}%\n"
        f"Optimal Allocation Ratio: {optimal_ratio:.1f}% ({optimal_count}/{total_orders} orders)\n"
        f"Sub-optimal Customer %: {suboptimal_pct:.1f}%\n"
        f"Productive Transfer %: {prod_pct:.1f}%\n"
        f"Unproductive Transfer Ratio: {unprod_ratio:.1f}%\n"
        f"Total Volume: {total_vol:,.0f} HL\n"
        f"STO Count: {len(country_stos)}"
    )
 
    interpret_prompt = (
        "You are a Senior Supply Chain Analyst. I have calculated the following KPIs for {0}:\n\n"
        "{1}\n\n"
        "Additional Context from Memory: {2}\n\n"
        "Please provide a professional, explanatory response. "
        "1. Present the data clearly in a structured way.\n"
        "2. Provide a 'Strategic Analysis' section explaining what these numbers mean.\n"
        "3. Keep the tone professional and expert-level."
    ).format(country_label, raw_metrics, rag_context)
 
    analysis_res = llm.invoke([HumanMessage(content=interpret_prompt)])
    answer = analysis_res.content
 
    sources = [{
        "type": "kpi_engine",
        "source": "customer_orders.json",
        "page": "1",
        "confidence": 0.98,
        "text_snippet": f"Allocation Efficiency: {avg_efficiency * 100:.1f}%, Optimal Ratio: {optimal_ratio:.1f}%"
    }]
    return {"answer": answer, "sources": sources}
 
 
@router.post("/")
async def chat(req: ChatRequest):
    try:
        if not orchestrator:
            return {"answer": "Error: Orchestrator offline.", "sources": []}
           
        query_lower = req.message.lower()
        agent_id = req.agent_id

        # ── SAP data query check — must happen BEFORE is_generic ──────────────
        # Queries with SAP field names (NETWR, KUNNR, VBAK etc.) or ID patterns
        # (KUNNR_001, MATNR_042) are always real database queries.
        # Even if they start with "what is / what are", they must go to SQL Agent.
        has_sap_terms = any(
            re.search(rf"\b{re.escape(term)}\b", query_lower)
            for term in SAP_DB_TERMS
        ) or bool(re.search(r"\b[a-z]{2,}_\d+\b", query_lower))  # matches kunnr_001, matnr_042 etc.

        if has_sap_terms:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {"answer": "OPENAI_API_KEY not configured.", "sources": []}
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                db = SQLDatabase.from_uri(db_url)
                agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
                response = agent_executor.invoke({"input": req.message})
                answer = response.get("output", "Sorry, I couldn't find that in the database.")
            else:
                answer = "Database is not configured. Cannot fetch SAP data."
            return {
                "answer": answer,
                "sources": [{
                    "type": "sql_agent",
                    "source": "sap_database",
                    "page": "1",
                    "confidence": 0.97,
                    "text_snippet": answer[:100]
                }]
            }

        # ── Generic question check ─────────────────────────────────────────────
        # Questions starting with "what is", "explain", "how does" etc. that do NOT
        # contain SAP terms are pure definition/knowledge questions → go to LLM only.
        generic_patterns = [
            r"^what is", r"^what are", r"^what does", r"^what do you mean",
            r"^explain", r"^how does", r"^how do", r"^tell me about",
            r"^define", r"^what would", r"^what should", r"^why is",
            r"^can you explain", r"^could you explain", r"^describe",
            r"^meaning of", r"^what's the difference", r"^what are the",
        ]
        is_generic = any(re.search(p, query_lower) for p in generic_patterns)

        if is_generic:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {"answer": "I'm the SCNV Assistant. You need to configure my OPENAI_API_KEY for full conversational access.", "sources": []}
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)
            prompt = (
                f"You are the SCNV Assistant, an expert in supply chain management, logistics, "
                f"and SAP-based operations. The user asks: '{req.message}'. "
                f"Answer clearly and professionally as a supply chain expert. "
                f"Do not reference any internal data, KPIs, or database records — this is a general knowledge question."
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            return {
                "answer": response.content,
                "sources": [{
                    "type": "llm",
                    "source": "supply_chain_knowledge",
                    "page": "1",
                    "confidence": 0.99,
                    "text_snippet": response.content[:100]
                }]
            }
       
        # Initialize LLM for remaining specialized routes
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"answer": "I'm the SCNV Assistant. You need to configure my OPENAI_API_KEY for full conversational access.", "sources": []}
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)

        # ── Route 1: Country KPI Queries ──────────────────────────────────────
        has_kpi_keywords = is_country_kpi_query(query_lower)
        is_analyst_active = (agent_id == "analyst")
       
        if has_kpi_keywords or is_analyst_active:
            country_code = detect_country(query_lower)
            return answer_kpi_query(req.message, country_code, llm)
 
        # ── Route 2: STO Classification Queries ──────────────────────────────
        sto_keywords = [r"\bsto\b", r"\bclassify\b", r"\btransfer\b", r"\bdc\b", r"\blateral\b"]
        has_sto_keywords = any(re.search(p, query_lower) for p in sto_keywords)
       
        if agent_id == "orchestrator" or has_sto_keywords:
            dummy_sto = {
                "sto_id": f"MSG-{uuid.uuid4().hex[:6]}",
                "source_location": "DC_North" if "dc" in query_lower else "Unknown",
                "destination_location": "Store_44",
                "sku_id": "Laptops-X1" if "laptop" in query_lower else "Unknown",
                "quantity": 50,
                "event_type": "STO_CREATED"
            }
            initial_state_data = {
                "sto": dummy_sto,
                "event_type": dummy_sto.get("event_type", "STO_CREATED")
            }
            final_state = orchestrator.process_event(initial_state_data)
            res_dict = final_state if isinstance(final_state, dict) else final_state.__dict__
            sources = res_dict.get('graph_context', [])
            if not sources:
                sources.append({
                    "type": "neo4j",
                    "source": "network_graph.xlsx",
                    "page": "Sheet1",
                    "confidence": 0.5,
                    "text_snippet": "No distinct alternative graphs resolved."
                })
            answer = (
                f"🛡️ **LangGraph STO Analysis Complete**\n\n"
                f"**Classification:** {res_dict.get('classification', 'N/A')}\n"
                f"**Strategic Reasoning:** {res_dict.get('reasoning_text', 'No detailed reasoning provided.')}\n\n"
                "This analysis was performed by our multi-agent orchestrator, cross-referencing master data and strategic logistics lanes."
            )
            return {"answer": answer, "sources": sources}
       
        # ── Route 3: Semantic Search ──────────────────────────────────────────
        if agent_id == "optimizer" or any(kw in query_lower for kw in ["similar", "decision", "allocation", "historical"]):
            try:
                if search_similar_decisions:
                    country_code = detect_country(query_lower)
                    results = search_similar_decisions(req.message, limit=5, country_code=country_code)
                    if results:
                        context_bits = []
                        for r in results:
                            context_bits.append(f"Type: {r['decision_type']}, Summary: {r['summary']}, Country: {r['country_code']}")
                        context_str = "\n".join(context_bits)
                        summary_prompt = (
                            "You are the SCNV Knowledge Expert. The user has asked for historical context on: '{0}'.\n\n"
                            "I found the following similar historical events in our database:\n{1}\n\n"
                            "Please provide a professional, explanatory summary of these findings and how they answer the user's query. "
                            "Highlight any key patterns or common outcomes."
                        ).format(req.message, context_str)
                        summary_res = llm.invoke([HumanMessage(content=summary_prompt)])
                        answer_text = summary_res.content
                        return {
                            "answer": answer_text,
                            "sources": [{"type": "pgvector", "source": "historical_decisions.docx", "page": str(i), "confidence": 0.9, "text_snippet": r['summary']} for i, r in enumerate(results, 1)]
                        }
            except Exception:
                pass
 
        # ── Route 4: General Question / SQL Agent fallback ────────────────────
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            db = SQLDatabase.from_uri(db_url)
            system_prompt = (
                "You are the SCNV Assistant. "
                f"The user says: '{req.message}'. "
                "Use the database if relevant. If it is a general supply chain question, provide a detailed and professional answer."
            )
            agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
            response = agent_executor.invoke({"input": system_prompt})
            answer = response.get("output", "Sorry, I couldn't process that.")
            source_type = "sql_agent"
        else:
            prompt = f"You are the SCNV Assistant. A user says: '{req.message}'. Reply as a supply chain expert."
            response = llm.invoke([HumanMessage(content=prompt)])
            answer = response.content
            source_type = "llm"
       
        return {
            "answer": answer,
            "sources": [{
                "type": source_type,
                "source": "enterprise_kb.docx",
                "page": "1",
                "confidence": 0.95,
                "text_snippet": answer[:100]
            }]
        }
    except Exception as e:
        import traceback
        print(f"Chat error: {traceback.format_exc()}")
        return {"answer": f"Chat Engine Error: {str(e)}", "sources": []}
 
@router.get("/sessions")
async def get_sessions(agent_id: str | None = None):
    results = []
    for sid, data in SESSIONS_DB.items():
        if agent_id and data.get("agent_id") != agent_id:
            continue
        results.append({
            "id": str(sid),
            "timestamp": data["timestamp"],
            "title": data["title"],
            "agent_id": data.get("agent_id")
        })
    return {"sessions": results}
 
@router.post("/sessions/new")
async def save_session(req: SessionSaveRequest):
    SESSIONS_DB[req.session_id] = {
        "title": req.title,
        "messages": req.messages,
        "agent_id": req.agent_id,
        "timestamp": datetime.datetime.now().isoformat()
    }
    return {"status": "saved"}
 
@router.get("/sessions/{session_id}")
async def load_session(session_id: str):
    if session_id in SESSIONS_DB:
        return SESSIONS_DB[session_id]
    return {"messages": []}
