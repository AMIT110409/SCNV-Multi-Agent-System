from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import datetime

class STOEvent(BaseModel):
    """
    The base input STO event format from the Perception layer.
    """
    sto_id: str
    source_location: str
    destination_location: str
    sku_id: str
    quantity: float
    creation_date: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class A2AMessage(BaseModel):
    """
    Standardized Agent-to-Agent message protocol.
    """
    sender: str
    receiver: str
    message_type: str # REQUEST, RESPONSE, ESCALATION, QUERY
    payload: Dict[str, Any]
    confidence: float = 0.0
    trace_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class AgentState(BaseModel):
    """
    The LangGraph State object that is passed down the pipeline.
    """
    event_type: str = "STO_CREATED"  # STO_CREATED, SO_CREATED, DELIVERY_CREATED, CRON_DAILY
    sto: Optional[Dict[str, Any]] = None
    so: Optional[Dict[str, Any]] = None
    country_code: Optional[str] = None
    
    messages: List[A2AMessage] = []
    
    # Final synthesized outcomes
    classification: Optional[str] = None
    rule_applied: Optional[int] = None
    root_cause: Optional[str] = None
    confidence: float = 0.0
    reasoning_text: Optional[str] = None
    
    # Extracted data from sub-agents
    optimal_route: Optional[Dict[str, Any]] = None
    process_mining_insights: Optional[Dict[str, Any]] = None
    graph_context: List[Dict[str, Any]] = []
    
    # SO allocation efficiency
    is_optimal_allocation: Optional[bool] = None
    optimal_plant: Optional[str] = None
    allocation_efficiency_score: Optional[float] = None
    
    # Country KPI results
    country_kpi_results: Optional[Dict[str, Any]] = None
    
    # Control flags
    requires_escalation: bool = False
    ready_for_sap: bool = False
    
    def add_message(self, msg: A2AMessage):
        self.messages.append(msg)
