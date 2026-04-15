import os
import json
from sqlalchemy import text
import sys

# Add backend to path
sys.path.append(r"C:\Users\Abcom\Downloads\SCNV-Multi-Agent-System\SCNV-Multi-Agent-System-Anushka\backend")

from database import engine

def test_health():
    # 1. Check Database
    db_status = "unconnected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Check Data Files
    data_dir = os.path.abspath(r"C:\Users\Abcom\Downloads\SCNV-Multi-Agent-System\SCNV-Multi-Agent-System-Anushka\data\synthetic\gap_extended")
    files_missing = []
    required_files = ["incoming_stos_extended.json", "customer_orders.json", "plant_country_master.json"]
    for f in required_files:
        if not os.path.exists(os.path.join(data_dir, f)):
            files_missing.append(f)

    health = {
        "status": "healthy" if db_status == "connected" and not files_missing else "degraded",
        "database": db_status,
        "data_files": {
            "path": data_dir,
            "missing": files_missing,
            "found_all": len(files_missing) == 0
        }
    }
    print(json.dumps(health, indent=2))

if __name__ == "__main__":
    test_health()
