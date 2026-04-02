import sys
import os
from typing import Dict, Any
 
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "tools"))
from master_data import check_master_data
from strategic_matrix import check_strategic_matrix
 
# LangGraph specific imports
from protocol import AgentState, A2AMessage
import datetime
 
class SCMAnalystAgent:
    """
    Wraps the Rules 1-4 STO Classification logic for LangGraph.
    Takes AgentState as input, outputs modified AgentState.
    """
    def __init__(self):
        # We can reuse the internal logic from the STOClassifier
        pass
       
    def _internal_classify(self, sto: Dict[str, Any]) -> Dict[str, Any]:
        source = sto.get('source_location')
        dest = sto.get('destination_location')
        sku = sto.get('sku_id')
       
        source_md = check_master_data(sku, source)
        dest_md = check_master_data(sku, dest)
        source_is_plant = source_md.get('destination_plant_exists', False)
        dest_is_plant = dest_md.get('destination_plant_exists', False)
        #defined properly the rules
        if not source_is_plant and not dest_is_plant:
            return {"c": "UNPRODUCTIVE", "r": 2, "rc": "Incorrect Deployments", "txt": "This transfer is a lateral movement between two Distribution Centers (DC to DC), which is generally considered unproductive as it doesn't move goods closer to the final customer and increases handling costs."}
           
        if not source_is_plant and dest_is_plant:
            return {"c": "UNPRODUCTIVE", "r": 3, "rc": "Incorrect Deployments", "txt": "This is a reverse movement from a Distribution Center back to a Production Plant. This indicates a sub-optimal flow as products should ideally flow downstream towards customers."}
           
        if source_is_plant and not dest_is_plant:
            lane_info = check_strategic_matrix(source, dest)
            if lane_info.get("is_strategic_lane") and lane_info.get("capacity_utilization", 0.0) < 0.95:
                return {"c": "PRODUCTIVE", "r": 1, "rc": "None", "txt": "This is a standard productive flow from a Production Plant to a Distribution Center along a designated strategic lane with available capacity."}
            else:
                return {"c": "UNPRODUCTIVE", "r": 1, "rc": "Sales Over Forecast", "txt": "While this is a Plant to DC movement, it is classified as unproductive because it falls outside of strategic lanes or indicates a push due to sales exceeding forecasts, potentially leading to inventory imbalances."}
 
        if source_is_plant and dest_is_plant:
            if dest_md.get("source_model") == "DUAL":
                return {"c": "UNPRODUCTIVE", "r": 4, "rc": "Planning Error", "txt": "This Plant to Plant transfer is flagged as unproductive because the destination uses a Dual Sourcing model, which should have been managed through more efficient direct allocations."}
            elif dest_md.get("source_model") == "SINGLE":
                if not dest_md.get("is_sourcing_plant"):
                    return {"c": "PRODUCTIVE", "r": 4, "rc": "None", "txt": "Movement from a sourcing Plant to a non-sourcing Plant in a Single Sourcing model. This is necessary to balance network inventory."}
                else:
                    return {"c": "UNPRODUCTIVE", "r": 4, "rc": "Incorrect Deployments", "txt": "Detected a reverse single-sourcing flow (Plant to Sourcing Plant), which is contrary to the defined supply chain strategy."}
 
        return {"c": "UNKNOWN", "r": 0, "rc": "Unknown", "txt": "Escalate"}
 
    def invoke(self, state: AgentState) -> AgentState:
        """
        LangGraph Node invocation function
        """
        sto = state.sto
        res = self._internal_classify(sto)
       
        # Format the A2A Message
        msg = A2AMessage(
            sender="scm_analyst",
            receiver="orchestrator",
            message_type="RESPONSE",
            payload=res,
            confidence=1.0 if res["c"] != "UNKNOWN" else 0.0,
            trace_id=sto.get("sto_id", "unknown")
        )
       
        # Update State
        state.add_message(msg)
        state.classification = res["c"]
        state.rule_applied = res["r"]
        state.root_cause = res["rc"]
        state.reasoning_text = res["txt"]
        state.confidence = msg.confidence
       
        return state
 
# Fallback for old standalone testing if needed
class STOClassifier(SCMAnalystAgent):
    def classify_sto(self, sto: Dict[str, Any]) -> Dict[str, Any]:
        res = self._internal_classify(sto)
        return {
            "sto_id": sto.get("sto_id"),
            "classification": res["c"],
            "rule_applied": res["r"],
            "root_cause": res["rc"],
            "confidence": 1.0 if res["c"] != "UNKNOWN" else 0.0,
            "reasoning_text": res["txt"]
        }