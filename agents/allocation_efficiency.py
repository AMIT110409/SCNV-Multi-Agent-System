import os
import sys
import json
from typing import Dict, Any

# Ensure we can import from the agents dir
sys.path.append(os.path.dirname(__file__))
from protocol import AgentState, A2AMessage

class AllocationEfficiencyAgent:
    """
    Agent responsible for monitoring customer Sales Orders and shipments.
    Calculates efficiency of allocations based on the strategic matrix.
    """
    def __init__(self):
        self.agent_name = "AllocationEfficiencyAgent"
        
        # Load synthetic data for checks
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "gap_extended")
        
        self.plants = []
        if os.path.exists(os.path.join(data_dir, "plant_country_master.json")):
            with open(os.path.join(data_dir, "plant_country_master.json"), "r") as f:
                self.plants = json.load(f)
                
    def check_optimal_source_for_customer(self, so: Dict[str, Any]) -> tuple:
        """
        Given a sales order (or delivery), identify the optimal source 
        plant based on the country and strategic capacity.
        Returns: (optimal_plant_werks, score)
        """
        target_country = so.get("country_code")
        if not target_country:
            return None, 0.0
            
        # Filter plants by country
        eligible_plants = [p for p in self.plants if p.get("LAND1") == target_country]
        if not eligible_plants:
            return None, 0.0
            
        # Score plants based on purely synthetic criteria (strategic flag and occupancy)
        def score_plant(p):
            base_score = 0.5
            if p.get("STRATEGIC_FLAG") == "Y":
                base_score += 0.3
            
            # Prefer less occupancy
            occupancy = p.get("CURRENT_OCCUPANCY_PCT", 100)
            if occupancy < 80:
                base_score += 0.2
            elif occupancy > 90:
                base_score -= 0.2
                
            return min(1.0, max(0.0, base_score))
            
        scored = [(p, score_plant(p)) for p in eligible_plants]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        best_plant, best_score = scored[0]
        return best_plant.get("WERKS"), best_score

    def invoke(self, state: AgentState) -> AgentState:
        """
        Main execution point for the state graph.
        """
        if state.event_type not in ["SO_CREATED", "DELIVERY_CREATED"]:
            # Only process relevant events
            return state
            
        so = state.so
        if not so:
            return state
            
        optimal_werks, score = self.check_optimal_source_for_customer(so)
        assigned_werks = so.get("assigned_plant")
        
        state.optimal_plant = optimal_werks
        state.allocation_efficiency_score = score
        state.is_optimal_allocation = (optimal_werks == assigned_werks) if optimal_werks else True
        
        # Add message
        msg = A2AMessage(
            sender=self.agent_name,
            receiver="Orchestrator",
            message_type="RESPONSE",
            payload={"is_optimal_allocation": state.is_optimal_allocation, "score": score},
            confidence=score,
            trace_id=f"trace_ae_{so.get('so_number', 'unknown')}"
        )
        state.add_message(msg)
        
        return state
