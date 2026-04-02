from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import os
import sys

# Ensure backend root is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from auth_deps import verify_supabase_jwt

from sqlalchemy import create_engine, MetaData, select
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

# Explicitly load .env from the backend root
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

router = APIRouter()

# Initialize DB connection dynamically to query nodes
db_url = os.getenv('DATABASE_URL')
engine = None
metadata = MetaData()

if db_url:
    try:
        engine = create_engine(db_url)
        metadata.reflect(bind=engine)
    except Exception as e:
        print(f"Warning: Failed to reflect metadata for network map: {e}")

@router.get("/map")
async def get_network_map(user_data: dict = Depends(verify_supabase_jwt)):
    """
    Returns the real SAP network structural data from Supabase for the frontend to render.
    Requires authentication.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection string not configured.")
        
    try:
        nodes = []
        edges = []
        
        # We need plants and DCs to represent physical locations on the map.
        with engine.connect() as conn:
            # 1. Fetch Plants (Sources)
            if 'plant_master' in metadata.tables:
                plant_table = metadata.tables['plant_master']
                plants = conn.execute(select(plant_table)).fetchall()
                for i, plant in enumerate(plants):
                    nodes.append({
                        "id": plant.plant_id,
                        "type": "plant",
                        "data": {
                            "label": f"Plant {plant.country} ({plant.region})" if plant.country else "Plant",
                            "type": "manufacturing"
                        },
                        # Grid layout for Plants: 4 columns wide
                        "position": {"x": (i % 4) * 280, "y": (i // 4) * 150}
                    })

            # 2. Fetch DCs (Destinations)
            if 'dc_master' in metadata.tables:
                dc_table = metadata.tables['dc_master']
                dcs = conn.execute(select(dc_table)).fetchall()
                for i, dc in enumerate(dcs):
                    nodes.append({
                        "id": dc.dc_id,
                        "type": "dc",
                        "data": {
                            "label": f"DC {dc.country}" if dc.country else "DC",
                            "type": "distribution"
                        },
                        # Grid layout for DCs: 6 columns wide, shifted 1500px to the right
                        "position": {"x": 1500 + (i % 6) * 280, "y": (i // 6) * 150}
                    })
            
            # 3. Create Edges based on STOs (or Strategic Matrix if that represents lanes)
            if 'strategic_matrix' in metadata.tables:
                lane_table = metadata.tables['strategic_matrix']
                lanes = conn.execute(select(lane_table).limit(100)).fetchall() # Limit to avoid overwhelming React Flow
                for lane in lanes:
                    edges.append({
                        "id": f"edge-{lane.id}",
                        "source": lane.source,
                        "target": lane.destination,
                        "animated": True,
                        "label": "Strategic Lane" if str(lane.is_strategic_lane).lower() == 'true' else "Standard Use",
                        "style": {"stroke": "#4f46e5" if str(lane.is_strategic_lane).lower() == 'true' else "#9ca3af"}
                    })

        return {
            "status": "success",
            "nodes": nodes,
            "edges": edges
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
