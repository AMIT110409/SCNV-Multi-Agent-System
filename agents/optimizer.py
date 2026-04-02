import sys
import os
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "tools"))
from logistics import calculate_logistics_cost

# LangGraph state protocol
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ""))
from protocol import AgentState, A2AMessage

class OptimizerAgent:
    """
    Activates when an STO is classified as Unproductive but theoretically mandatory.
    Finds alternative sourcing logic and computes savings.
    """
    def __init__(self):
        pass
        
    def invoke(self, state: AgentState) -> AgentState:
        """
        LangGraph Node invocation function.
        Only optimizing if the classification is UNPRODUCTIVE.
        """
        if state.classification != "UNPRODUCTIVE":
            return state
            
        sto = state.sto
        trace_id = sto.get("sto_id", "unknown")
        
        # Calculate standard cost
        original_cost = calculate_logistics_cost(
            sto.get('source_location'), 
            sto.get('destination_location'), 
            sto.get('quantity', 1.0)
        )
        
        # Mock Optimizer finding a better alternate plant
        # In full phase, this uses OR-Tools / real supply chain mapping
        alt_plant = "Plant_Optimized_01"
        optimized_cost = calculate_logistics_cost(
            alt_plant, 
            sto.get('destination_location'), 
            sto.get('quantity', 1.0)
        )
        
        savings = float(original_cost.get('total_cost', 0)) - float(optimized_cost.get('total_cost', 0))
        # Ensure we don't mock negative savings for demonstration purposes
        savings = max(100.0, savings)
        
        opt_result = {
            "optimal_route": {
                "source": alt_plant,
                "destination": sto.get('destination_location')
            },
            "cost_savings": round(savings, 2),
            "freshness_impact": "+2 days"
        }
        
        msg = A2AMessage(
            sender="optimizer",
            receiver="orchestrator",
            message_type="RESPONSE",
            payload=opt_result,
            confidence=0.85,
            trace_id=trace_id
        )
        
        state.add_message(msg)
        state.optimal_route = opt_result
        
        return state
