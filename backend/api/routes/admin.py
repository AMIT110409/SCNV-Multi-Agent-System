from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class CelonisToggleRequest(BaseModel):
    active: bool

# Global config state (in-memory for MVP)
config_state = {
    "celonis_integration_active": False
}

@router.post("/celonis/toggle")
async def toggle_celonis(req: CelonisToggleRequest):
    config_state["celonis_integration_active"] = req.active
    print(f"[BACKEND] Celonis Integration configured to: {req.active}")
    return {
        "success": True, 
        "status": req.active,
        "message": f"Celonis integration is now {'active' if req.active else 'inactive'}"
    }
