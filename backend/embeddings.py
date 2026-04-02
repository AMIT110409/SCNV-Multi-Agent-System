"""
embeddings.py — pgvector embedding module for SO/STO allocation decisions.

Uses OpenAI text-embedding-3-small to generate 1536-dim vectors, stored in
the `decision_embeddings` table in Supabase PostgreSQL with pgvector.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ── OpenAI Embedding Client ────────────────────────────────────────────────────

def get_embedding(text: str) -> List[float]:
    """Generate a 1536-dim embedding using OpenAI text-embedding-3-small."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# ── Decision Text Builders ─────────────────────────────────────────────────────

def build_so_decision_text(so: Dict[str, Any]) -> str:
    """Convert a Sales Order allocation decision into a searchable text summary."""
    optimal = "optimally" if so.get("is_optimal_allocation") else "sub-optimally"
    score = so.get("allocation_efficiency_score", 0)
    return (
        f"Sales Order {so.get('so_number', 'N/A')} for customer {so.get('customer_number', 'N/A')} "
        f"in country {so.get('country_code', 'N/A')}. "
        f"Material {so.get('material_number', 'N/A')}, quantity {so.get('quantity_hl', 0)} HL. "
        f"Assigned to plant {so.get('assigned_plant', 'N/A')}, "
        f"optimal plant is {so.get('optimal_plant', 'N/A')}. "
        f"Allocation was {optimal} with efficiency score {score:.2f}. "
        f"Order date: {so.get('order_date', 'N/A')}, Planned GI: {so.get('planned_gi_date', 'N/A')}."
    )


def build_sto_decision_text(sto: Dict[str, Any]) -> str:
    """Convert an STO classification decision into a searchable text summary."""
    movement = sto.get("movement_type", "N/A")
    is_productive = sto.get("movement_type") == "641" and sto.get("is_pre_goods_issue")
    status = "productive" if is_productive else "unproductive"
    return (
        f"Stock Transfer Order {sto.get('sto_id', 'N/A')} in country {sto.get('COUNTRY_CODE', 'N/A')}. "
        f"From {sto.get('source_location', 'N/A')} to {sto.get('destination_location', 'N/A')}. "
        f"Volume {sto.get('VOLUME_HL', 0)} HL, movement type {movement}. "
        f"Transfer classified as {status}. "
        f"Confidence score: {sto.get('CONFIDENCE_SCORE', 0):.2f}. "
        f"Created: {sto.get('creation_date', 'N/A')}."
    )


# ── Embed Decision Functions ───────────────────────────────────────────────────

def embed_so_decision(so: Dict[str, Any]) -> Dict[str, Any]:
    """Generate embedding for an SO allocation decision."""
    text = build_so_decision_text(so)
    embedding = get_embedding(text)
    return {
        "decision_type": "SO_ALLOCATION",
        "decision_id": so.get("so_number", ""),
        "country_code": so.get("country_code", ""),
        "summary_text": text,
        "embedding": embedding,
        "metadata": json.dumps({
            "customer": so.get("customer_number"),
            "assigned_plant": so.get("assigned_plant"),
            "optimal_plant": so.get("optimal_plant"),
            "is_optimal": so.get("is_optimal_allocation"),
            "efficiency_score": so.get("allocation_efficiency_score"),
        })
    }


def embed_sto_decision(sto: Dict[str, Any]) -> Dict[str, Any]:
    """Generate embedding for an STO classification decision."""
    text = build_sto_decision_text(sto)
    embedding = get_embedding(text)
    is_productive = sto.get("movement_type") == "641" and sto.get("is_pre_goods_issue")
    return {
        "decision_type": "STO_CLASSIFICATION",
        "decision_id": sto.get("sto_id", ""),
        "country_code": sto.get("COUNTRY_CODE", ""),
        "summary_text": text,
        "embedding": embedding,
        "metadata": json.dumps({
            "movement_type": sto.get("movement_type"),
            "is_productive": is_productive,
            "volume_hl": sto.get("VOLUME_HL"),
            "confidence": sto.get("CONFIDENCE_SCORE"),
        })
    }


# ── Similarity Search ──────────────────────────────────────────────────────────

def search_similar_decisions(
    query: str,
    limit: int = 5,
    decision_type: Optional[str] = None,
    country_code: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar allocation/classification decisions using pgvector
    cosine similarity.
    """
    from sqlalchemy import create_engine, text

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return []

    engine = create_engine(db_url)
    query_embedding = get_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Build SQL with optional filters
    filters = []
    params = {"embedding": embedding_str, "limit": limit}

    if decision_type:
        filters.append("decision_type = :decision_type")
        params["decision_type"] = decision_type
    if country_code:
        filters.append("country_code = :country_code")
        params["country_code"] = country_code

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    sql = text(f"""
        SELECT decision_id, decision_type, country_code, summary_text, metadata,
               1 - (embedding <=> :embedding::vector) AS similarity
        FROM decision_embeddings
        {where_clause}
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    results = []
    for row in rows:
        results.append({
            "decision_id": row[0],
            "decision_type": row[1],
            "country_code": row[2],
            "summary": row[3],
            "metadata": json.loads(row[4]) if row[4] else {},
            "similarity": round(float(row[5]), 4) if row[5] else 0.0,
        })
    return results
