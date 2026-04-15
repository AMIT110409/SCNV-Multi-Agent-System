import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Integer, insert
import math

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(db_url)
metadata = MetaData()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic')

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), 'r') as f:
        return json.load(f)

# Define schemas based on the JSON structures
dc_master_table = Table(
    'dc_master', metadata,
    Column('dc_id', String, primary_key=True),
    Column('name', String),
    Column('country', String)
)

plant_master_table = Table(
    'plant_master', metadata,
    Column('plant_id', String, primary_key=True),
    Column('country', String),
    Column('region', String)
)

incoming_stos_table = Table(
    'incoming_stos', metadata,
    Column('sto_id', String, primary_key=True),
    Column('source_location', String),
    Column('destination_location', String),
    Column('sku_id', String),
    Column('quantity', Float),
    Column('creation_date', String)
)

sku_master_table = Table(
    'sku_master', metadata,
    Column('sku_id', String, primary_key=True),
    Column('material_type', String),
    Column('source_model', String),
    Column('shelf_life_days', Integer)
)

strategic_matrix_table = Table(
    'strategic_matrix', metadata,
    # Composite primary key conceptually, simple insert here. We'll let SQLAlchemy auto-handle if no PK specified for bulk insert in Postgres.
    Column('id', Integer, primary_key=True, autoincrement=True), 
    Column('source', String),
    Column('destination', String),
    Column('is_strategic_lane', String), # Boolean comes in as True/False JSON, Postgres boolean fits but String avoids mapping errors easily
    Column('capacity_utilization', Float)
)

def create_tables():
    print("Creating tables if they do not exist...")
    metadata.create_all(engine)
    print("Tables ready.")

def insert_data(table, data, chunk_size=1000):
    with engine.begin() as conn:
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            # Replace 'nan' strings with None, and handle python float nan
            cleaned_chunk = []
            for row in chunk:
                cleaned_row = {}
                for k, v in row.items():
                    if k == 'sourcing_plants' and table.name == 'sku_master':
                         continue # We drop the array for simple relational insert, or we'd need a one-to-many table.
                    if isinstance(v, str) and v.lower() == 'nan':
                        cleaned_row[k] = None
                    elif isinstance(v, float) and math.isnan(v):
                        cleaned_row[k] = None
                    elif isinstance(v, bool):
                        cleaned_row[k] = str(v)
                    else:
                        cleaned_row[k] = v
                cleaned_chunk.append(cleaned_row)
            
            # Using PostgreSQL-specific ON CONFLICT DO NOTHING to ensure idempotence
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            
            # Note: This code works for PostgreSQL/Supabase.
            # If used with SQLite, we would need different syntax.
            stmt = pg_insert(table).values(cleaned_chunk)
            on_conflict_stmt = stmt.on_conflict_do_nothing()
            
            conn.execute(on_conflict_stmt)
            print(f"Synced {i + len(chunk)}/{len(data)} records into {table.name} (Idempotent)...")

if __name__ == '__main__':
    print("Starting SAP Data Migration to Supabase via SQLAlchemy...")
    create_tables()
    
    try:
        dc_data = load_json('dc_master.json')
        print(f"Loaded {len(dc_data)} DC records.")
        insert_data(dc_master_table, dc_data)

        plant_data = load_json('plant_master.json')
        print(f"Loaded {len(plant_data)} Plant records.")
        insert_data(plant_master_table, plant_data)

        sto_data = load_json('incoming_stos.json')
        print(f"Loaded {len(sto_data)} STO records.")
        insert_data(incoming_stos_table, sto_data)
        
        sku_data = load_json('sku_master.json')
        print(f"Loaded {len(sku_data)} SKU records.")
        insert_data(sku_master_table, sku_data)
        
        matrix_data = load_json('strategic_matrix.json')
        print(f"Loaded {len(matrix_data)} Strategy Matrix records.")
        insert_data(strategic_matrix_table, matrix_data)

        print("Migration complete!")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        if hasattr(e, 'orig'):
            print(f"Original DBAPI error: {e.orig}")
