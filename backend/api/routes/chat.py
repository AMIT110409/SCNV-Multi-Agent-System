from fastapi import APIRouter
from pydantic import BaseModel
import uuid
import datetime

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    agent_id: str | None = None

class SessionSaveRequest(BaseModel):
    session_id: str
    title: str
    messages: list
    agent_id: str | None = None

SESSIONS_DB = {}

import sys
import os
import re
import json
import uuid
import datetime
import traceback
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.messages import HumanMessage

agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents"))
if agents_dir not in sys.path:
    sys.path.append(agents_dir)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from orchestrator import Orchestrator
    orchestrator = Orchestrator()
except Exception as e:
    print(f"Warning: Orchestrator failed to load: {e}")
    orchestrator = None

try:
    from embeddings import search_similar_decisions
except ImportError:
    search_similar_decisions = None

# ── KPI Data Loading ───────────────────────────────────────────────────────────
KPI_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/synthetic/gap_extended"))

def _load_kpi_json(filename):
    path = os.path.join(KPI_DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

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

SAP_DB_TERMS = [
    "netwr", "kunnr", "vbeln", "matnr", "werks", "vbak", "vbap",
    "likp", "lips", "mara", "marc", "mchb", "ekko", "ekpo",
    "lifnr", "bukrs", "waers", "menge", "posnr", "auart",
    "erdat", "erzet", "vkorg", "vtweg", "spart", "knumv",
    "kbetr", "kwmeng", "lfimg", "ntgew", "brgew",
]

def detect_country(query_lower: str) -> str | None:
    for name, code in sorted(COUNTRY_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(name)}\b", query_lower):
            return code
    return None

def answer_kpi_query(query: str, country_code: str | None, llm) -> dict:
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


# ── NEW: LLM-based intent classifier — replaces ALL keyword lists ──────────────
def classify_intent(message: str, agent_id: str | None) -> str:
    """
    Uses GPT to classify the user message into one of 6 routes.
    This replaces all hardcoded keyword lists and regex patterns.
    Returns: 'greeting' | 'kpi' | 'sto' | 'sap_data' | 'historical' | 'generic'
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "generic"

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)

    prompt = f"""You are a routing classifier for a Supply Chain AI assistant called SCNV.
Classify the user message into EXACTLY one of these routes:

1. "greeting"   — small talk, greetings, thanks, bye, how are you, what is the date/time, who are you, what can you do
2. "kpi"        — asking about KPIs, allocation efficiency, productive/unproductive transfer percentages,
                  country-level supply chain metrics, suboptimal customer %, volume data, monthly trends
3. "sto"        — asking to classify, analyze, or check a Stock Transfer Order (STO),
                  transfer between locations, DC to DC, plant to DC, lateral movements
4. "sap_data"   — asking about specific SAP field names (NETWR, KUNNR, VBAK, MATNR etc.)
                  or specific record IDs like KUNNR_001, VBAK_042
5. "historical" — asking for similar past decisions, historical cases, previous allocations, memory search
6. "generic"    — general supply chain knowledge, definitions, explanations, how things work, anything else

Current agent context: {agent_id or "none"}

User message: "{message}"

Reply with ONLY the single route word. Nothing else. Example reply: kpi"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        route = response.content.strip().lower()
        valid = {"greeting", "kpi", "sto", "sap_data", "historical", "generic"}
        return route if route in valid else "generic"
    except Exception:
        return "generic"


@router.post("/")
async def chat(req: ChatRequest):
    try:
        if not orchestrator:
            return {"answer": "Error: Orchestrator offline.", "sources": []}

        agent_id = req.agent_id

        # ── Single intelligent routing call — replaces all keyword checks ─────
        route = classify_intent(req.message, agent_id)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"answer": "OPENAI_API_KEY not configured.", "sources": []}
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)

        # ── Route: greeting ───────────────────────────────────────────────────
        if route == "greeting":
            response = llm.invoke([HumanMessage(content=(
                f"You are the SCNV Assistant for OFI Services, an AI-powered supply chain platform. "
                f"The user says: '{req.message}'. "
                f"Reply in a friendly and professional way in 1-2 sentences. "
                f"If it is a greeting, greet back and mention you can help with STO classification, "
                f"KPI analysis, allocation efficiency, and historical supply chain decisions."
            ))])
            return {"answer": response.content, "sources": []}

        # ── Route: kpi ────────────────────────────────────────────────────────
        if route == "kpi":
            country_code = detect_country(req.message.lower())
            return answer_kpi_query(req.message, country_code, llm)

        # ── Route: sto ────────────────────────────────────────────────────────
        if route == "sto":
            source_match = re.search(r'from\s+([\w_]+)', req.message, re.IGNORECASE)
            dest_match = re.search(r'to\s+([\w_]+)', req.message, re.IGNORECASE)
            qty_match = re.search(r'(\d+)\s*(hl|units|cases)?', req.message, re.IGNORECASE)
            sto_id_match = re.search(r'\b(STO[-_]?\w+|MSG[-_]?\w+)\b', req.message, re.IGNORECASE)

            parsed_sto = {
                "sto_id": sto_id_match.group(1) if sto_id_match else f"MSG-{uuid.uuid4().hex[:6]}",
                "source_location": source_match.group(1) if source_match else "DC_Unknown",
                "destination_location": dest_match.group(1) if dest_match else "DC_Unknown",
                "sku_id": "Beer_Generic",
                "quantity": float(qty_match.group(1)) if qty_match else 50,
                "event_type": "STO_CREATED"
            }

            final_state = orchestrator.process_event({
                "sto": parsed_sto,
                "event_type": "STO_CREATED"
            })
            res_dict = final_state if isinstance(final_state, dict) else final_state.__dict__

            sources = res_dict.get('graph_context', [])
            if not sources:
                sources = [{
                    "type": "neo4j",
                    "source": "network_graph.xlsx",
                    "page": "Sheet1",
                    "confidence": 0.5,
                    "text_snippet": "No distinct alternative graphs resolved."
                }]

            optimal_route_text = ""
            if res_dict.get('optimal_route'):
                optimal_route_text = (
                    f"\n\n**Optimal Route:** {res_dict['optimal_route'].get('source')} → "
                    f"{res_dict['optimal_route'].get('destination')}\n"
                    f"**Estimated Savings:** ${res_dict['optimal_route'].get('cost_savings', 0):,.2f}"
                )

            answer = (
                f"**STO Analysis: {parsed_sto['sto_id']}**\n\n"
                f"**Route:** {parsed_sto['source_location']} → {parsed_sto['destination_location']}\n"
                f"**Classification:** {res_dict.get('classification', 'N/A')}\n"
                f"**Root Cause:** {res_dict.get('root_cause', 'N/A')}\n"
                f"**Confidence:** {res_dict.get('confidence', 0) * 100:.0f}%\n\n"
                f"**Analysis:** {res_dict.get('reasoning_text', 'No reasoning provided.')}"
                f"{optimal_route_text}"
            )
            return {"answer": answer, "sources": sources}

        # ── Route: sap_data ───────────────────────────────────────────────────
        if route == "sap_data":
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

        # ── Route: historical ─────────────────────────────────────────────────
        if route == "historical":
            try:
                if search_similar_decisions:
                    country_code = detect_country(req.message.lower())
                    results = search_similar_decisions(req.message, limit=5, country_code=country_code)
                    if results:
                        context_str = "\n".join([
                            f"Type: {r['decision_type']}, Summary: {r['summary']}, Country: {r['country_code']}"
                            for r in results
                        ])
                        summary_res = llm.invoke([HumanMessage(content=(
                            f"You are the SCNV Knowledge Expert. The user asked: '{req.message}'.\n\n"
                            f"Similar historical decisions found:\n{context_str}\n\n"
                            f"Summarize these findings professionally and explain how they relate to the user's question."
                        ))])
                        return {
                            "answer": summary_res.content,
                            "sources": [
                                {"type": "pgvector", "source": "historical_decisions", "page": str(i),
                                 "confidence": 0.9, "text_snippet": r['summary']}
                                for i, r in enumerate(results, 1)
                            ]
                        }
            except Exception:
                pass
            return {"answer": "No similar historical decisions found in memory.", "sources": []}

        # ── Route: generic ────────────────────────────────────────────────────
        response = llm.invoke([HumanMessage(content=(
            f"You are the SCNV Assistant, an expert in supply chain management, logistics, "
            f"and SAP-based operations. The user asks: '{req.message}'. "
            f"Answer clearly and professionally as a supply chain expert."
        ))])
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

    except Exception as e:
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
