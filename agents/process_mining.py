import sys
import os
from typing import Dict, Any

# LangGraph state protocol
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ""))
from protocol import AgentState, A2AMessage
from backend.config import settings

class ProcessMiningAgent:
    """
    Optional Celonis process mining agent. 
    Toggled via CELONIS_ENABLED in config.py.
    """
    def __init__(self):
        self.enabled = settings.CELONIS_ENABLED
        
    def invoke(self, state: AgentState) -> AgentState:
        """
        LangGraph Node invocation function.
        """
        if not self.enabled:
            return state
            
        sto = state.sto
        trace_id = sto.get("sto_id", "unknown")
        
        # In a real environment, this would call PyCelonis
        # For our stub, we return mock conformance data
        mock_insights = {
            "lane_efficiency_pct": 82.5,
            "conformance_score": 0.91,
            "variant_patterns": ["Standard", "Delayed GI"],
            "deviation_insights": "Frequent delays at destination DC."
        }
        
        msg = A2AMessage(
            sender="process_mining",
            receiver="orchestrator",
            message_type="RESPONSE",
            payload=mock_insights,
            confidence=0.9,
            trace_id=trace_id
        )
        
        state.add_message(msg)
        state.process_mining_insights = mock_insights
        
        # Process mining can slightly bump up confidence of the final decision
        state.confidence = min(1.0, state.confidence + 0.05)
        
        return state
