from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "agents"))
from scm_analyst import STOClassifier

# Import new API Routers
from api.routes import admin, chat, alerts, documents, network, kpi
from auth_deps import verify_supabase_jwt

# Database setup (Only used by agents/other models now; User model removed as Supabase handles auth)
from database import engine, Base

# Import SAP SO table models so they get auto-created
from models.sap_so_tables import VBAK, VBAP, LIKP, LIPS  # noqa: F401

# Create all tables in the database (EXCEPT users, which Supabase handles)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SCNV Agent API", description="Supply Chain Network Visibility Multi-Agent Backend")

# Add CORS Middleware to allow React/Vite Frontend (localhost:5173 / localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protect API routes matching frontend api.js by mandating the Supabase JWT
app.include_router(chat.router, prefix="/api/chat", tags=["Agent Chat"], dependencies=[Depends(verify_supabase_jwt)])
app.include_router(chat.router, prefix="/api/history", tags=["Chat History"], dependencies=[Depends(verify_supabase_jwt)])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Configuration"], dependencies=[Depends(verify_supabase_jwt)])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Human-in-the-loop Alerts"], dependencies=[Depends(verify_supabase_jwt)])
app.include_router(documents.router, prefix="/api/documents", tags=["Knowledge Base Ingestion"], dependencies=[Depends(verify_supabase_jwt)])
app.include_router(network.router, prefix="/api/network", tags=["Network Map"], dependencies=[Depends(verify_supabase_jwt)])
app.include_router(kpi.router, prefix="/api/kpi", tags=["KPI Analytics"], dependencies=[Depends(verify_supabase_jwt)])

class STOEvent(BaseModel):
    sto_id: str
    source_location: str
    destination_location: str
    sku_id: str
    quantity: float

classifier = STOClassifier()

@app.post("/stos/classify", summary="Classify a single STO event using Rules 1-4")
async def classify_sto(sto: STOEvent):
    """
    Receives an STO event, runs it through the deterministic Rules 1-4 engine, and returns the classification.
    """
    try:
        sto_dict = sto.dict()
        result = classifier.classify_sto(sto_dict)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System Diagnostics"])
async def health_check():
    from sqlalchemy import text
    from database import engine
    import os

    # 1. Check Database
    db_status = "unconnected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Check Data Files
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/synthetic/gap_extended"))
    files_missing = []
    required_files = ["incoming_stos_extended.json", "customer_orders.json", "plant_country_master.json"]
    for f in required_files:
        if not os.path.exists(os.path.join(data_dir, f)):
            files_missing.append(f)

    return {
        "status": "healthy" if db_status == "connected" and not files_missing else "degraded",
        "database": db_status,
        "data_files": {
            "path": data_dir,
            "missing": files_missing,
            "found_all": len(files_missing) == 0
        },
        "cwd": os.getcwd(),
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
