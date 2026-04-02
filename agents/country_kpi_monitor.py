import os
import sys
import json
from typing import Dict, Any

# Ensure we can import from the agents dir
sys.path.append(os.path.dirname(__file__))
from protocol import AgentState, A2AMessage

class CountryKPIMonitorAgent:
    """
    Agent responsible for aggregating country-level KPIs such as 
    productive transfer volumes and suboptimal customer percentages.
    Runs on a CRON schedule.
    """
    def __init__(self):
        self.agent_name = "CountryKPIMonitorAgent"
        
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "gap_extended")
        
        self.stos = []
        if os.path.exists(os.path.join(data_dir, "incoming_stos_extended.json")):
            with open(os.path.join(data_dir, "incoming_stos_extended.json"), "r") as f:
                self.stos = json.load(f)
                
    def aggregate_country_kpis(self, country_code: str) -> Dict[str, Any]:
        """
        Aggregate productive and unproductive volume for a given country.
        """
        country_stos = [s for s in self.stos if s.get("COUNTRY_CODE") == country_code]
        
        total_vol = 0.0
        prod_vol = 0.0
        
        for s in country_stos:
            vol = s.get("VOLUME_HL", 0.0)
            total_vol += vol
            # Synthetic classification logic (using movement type + random)
            # In a real scenario, this relies on SCM Analyst outputs
            if s.get("movement_type") == "641" and s.get("is_pre_goods_issue"):
                prod_vol += vol
                
        if total_vol > 0:
            productive_pct = (prod_vol / total_vol) * 100
        else:
            productive_pct = 0.0
            
        return {
            "country_code": country_code,
            "total_volume": total_vol,
            "productive_volume": prod_vol,
            "productive_pct": productive_pct,
            "sto_count": len(country_stos)
        }

    def invoke(self, state: AgentState) -> AgentState:
        """
        Main execution point for the state graph.
        """
        if state.event_type != "CRON_DAILY":
            return state
            
        target_country = state.country_code or "GB"
        
        kpis = self.aggregate_country_kpis(target_country)
        state.country_kpi_results = kpis
        
        msg = A2AMessage(
            sender=self.agent_name,
            receiver="Orchestrator",
            message_type="RESPONSE",
            payload={"kpis": kpis},
            confidence=1.0,
            trace_id=f"trace_kpi_{target_country}"
        )
        state.add_message(msg)
        
        return state
