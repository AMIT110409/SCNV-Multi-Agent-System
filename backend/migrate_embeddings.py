"""
migrate_embeddings.py — Batch migration script to:
1. Enable pgvector extension in Supabase PostgreSQL
2. Create the `decision_embeddings` table
3. Generate and insert embeddings for SO + STO decisions

Usage: cd backend && python migrate_embeddings.py
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import embedding functions
from embeddings import embed_so_decision, embed_sto_decision

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'gap_extended')


def get_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        sys.exit(1)
    return create_engine(db_url)


def setup_pgvector(engine):
    """Enable pgvector extension and create embeddings table."""
    with engine.begin() as conn:
        # Enable pgvector
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("[OK] pgvector extension enabled")

        # Create embeddings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS decision_embeddings (
                id SERIAL PRIMARY KEY,
                decision_type VARCHAR(30) NOT NULL,
                decision_id VARCHAR(50) NOT NULL,
                country_code VARCHAR(10),
                summary_text TEXT NOT NULL,
                metadata JSONB,
                embedding vector(1536) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(decision_type, decision_id)
            )
        """))
        print("[OK] decision_embeddings table created")

        # Create index for fast cosine similarity search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_decision_embeddings_cosine
            ON decision_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 20)
        """))
        print("[OK] IVFFlat cosine index created")


def insert_embedding(conn, record: dict):
    """Insert a single embedding record."""
    embedding_str = "[" + ",".join(str(x) for x in record["embedding"]) + "]"
    conn.execute(
        text("""
            INSERT INTO decision_embeddings (decision_type, decision_id, country_code, summary_text, metadata, embedding)
            VALUES (:decision_type, :decision_id, :country_code, :summary_text, :metadata, CAST(:embedding AS vector))
            ON CONFLICT (decision_type, decision_id) DO UPDATE SET
                summary_text = EXCLUDED.summary_text,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding
        """),
        {
            "decision_type": record["decision_type"],
            "decision_id": record["decision_id"],
            "country_code": record["country_code"],
            "summary_text": record["summary_text"],
            "metadata": record["metadata"],
            "embedding": embedding_str,
        }
    )


def migrate_so_decisions(engine):
    """Embed and insert SO allocation decisions."""
    filepath = os.path.join(DATA_DIR, "customer_orders.json")
    if not os.path.exists(filepath):
        print("⚠ customer_orders.json not found, skipping SO embeddings")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        orders = json.load(f)

    print(f"\nEmbedding {len(orders)} SO allocation decisions...")
    with engine.begin() as conn:
        for i, so in enumerate(orders):
            try:
                record = embed_so_decision(so)
                insert_embedding(conn, record)
                print(f"  [{i+1}/{len(orders)}] SO {so.get('so_number')} [OK]")
                # Rate limiting for OpenAI API
                if (i + 1) % 10 == 0:
                    time.sleep(1)
            except Exception as e:
                print(f"  [{i+1}/{len(orders)}] SO {so.get('so_number')} [ERROR] Error: {e}")

    print(f"[OK] SO embeddings complete ({len(orders)} records)")


def migrate_sto_decisions(engine, max_stos: int = 50):
    """
    Embed and insert STO classification decisions.
    Limited to max_stos to control API costs (STOs can be 500+).
    """
    filepath = os.path.join(DATA_DIR, "incoming_stos_extended.json")
    if not os.path.exists(filepath):
        print("⚠ incoming_stos_extended.json not found, skipping STO embeddings")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        stos = json.load(f)

    # Take a representative sample across countries
    subset = stos[:max_stos]
    print(f"\nEmbedding {len(subset)} STO decisions (of {len(stos)} total, limited for cost)...")

    with engine.begin() as conn:
        for i, sto in enumerate(subset):
            try:
                record = embed_sto_decision(sto)
                insert_embedding(conn, record)
                print(f"  [{i+1}/{len(subset)}] STO {sto.get('sto_id')} [OK]")
                if (i + 1) % 10 == 0:
                    time.sleep(1)
            except Exception as e:
                print(f"  [{i+1}/{len(subset)}] STO {sto.get('sto_id')} [ERROR] Error: {e}")

    print(f"[OK] STO embeddings complete ({len(subset)} records)")


if __name__ == "__main__":
    print("=" * 60)
    print("  SCNV Agent — pgvector Embedding Migration")
    print("=" * 60)

    engine = get_engine()

    print("\n[Step 1] Setting up pgvector...")
    setup_pgvector(engine)

    print("\n[Step 2] Embedding SO allocation decisions...")
    migrate_so_decisions(engine)

    print("\n[Step 3] Embedding STO classification decisions...")
    migrate_sto_decisions(engine, max_stos=50)

    print("\n" + "=" * 60)
    print("  Migration complete! Run semantic search with:")
    print("  from embeddings import search_similar_decisions")
    print("  results = search_similar_decisions('UK allocation efficiency')")
    print("=" * 60)
