from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ExecuteActionRequest(BaseModel):
    action: str
    overrideReason: str | None = ""

# Mock STOs pending human review
MOCK_PENDING_STOS = [
    {
        "id": "STO-9921",
        "source": "DC_North",
        "destination": "Store_44",
        "item": "Laptops-X1",
        "quantity": 50,
        "reason": "High Risk - Lead Time Violation",
        "timestamp": "10 mins ago",
        "escalatesIn": "1h 50m",
        "status": "pending",
        "severity": "high"
    }
]

@router.get("/pending")
async def get_pending_alerts():
    return {"alerts": MOCK_PENDING_STOS}

@router.post("/{sto_id}/execute")
async def execute_sto_action(sto_id: str, action_req: ExecuteActionRequest):
    action = action_req.action
    reason = action_req.overrideReason
    
    print(f"[ALERTS MODULE] Processing STO {sto_id} with action '{action}'. Reason: {reason}")
    # In a real app, this updates Postgres and triggers PyCelonis/SAP webhook
    return {"status": "success", "sto_id": sto_id, "action": action, "logged_to_memory": True}


# ── SO Re-routing Alerts ────────────────────────────────────────────────────────

MOCK_PENDING_SOS = [
    {
        "id": "SO-2026-0451",
        "customer": "CUST087",
        "material": "Decorative Paints - Premium",
        "assigned_plant": "7C53",
        "optimal_plant": "DBAB",
        "country": "BE",
        "quantity_hl": 427.63,
        "reason": "Sub-optimal Allocation — Closer strategic plant available",
        "efficiency_score": 0.63,
        "timestamp": "5 mins ago",
        "escalatesIn": "2h 15m",
        "status": "pending",
        "severity": "medium"
    },
    {
        "id": "SO-2026-0452",
        "customer": "CUST066",
        "material": "Industrial Coatings - Marine",
        "assigned_plant": "30AA",
        "optimal_plant": "BE78",
        "country": "DE",
        "quantity_hl": 94.37,
        "reason": "Capacity Imbalance — Assigned plant at 92% occupancy",
        "efficiency_score": 0.61,
        "timestamp": "12 mins ago",
        "escalatesIn": "1h 48m",
        "status": "pending",
        "severity": "high"
    },
    {
        "id": "SO-2026-0453",
        "customer": "CUST112",
        "material": "Powder Coatings - Automotive",
        "assigned_plant": "A1F2",
        "optimal_plant": "GB91",
        "country": "GB",
        "quantity_hl": 253.10,
        "reason": "Non-Strategic Lane — Route violates strategic matrix",
        "efficiency_score": 0.55,
        "timestamp": "22 mins ago",
        "escalatesIn": "0h 38m",
        "status": "pending",
        "severity": "high"
    }
]


@router.get("/pending-so")
async def get_pending_so_alerts():
    """Return SO re-routing alerts pending human approval."""
    return {"alerts": MOCK_PENDING_SOS}


@router.post("/so/{so_id}/execute")
async def execute_so_action(so_id: str, action_req: ExecuteActionRequest):
    """Approve, reject, or override an SO re-routing decision."""
    action = action_req.action
    reason = action_req.overrideReason

    print(f"[ALERTS MODULE] Processing SO {so_id} with action '{action}'. Reason: {reason}")
    return {"status": "success", "so_id": so_id, "action": action, "logged_to_memory": True}

