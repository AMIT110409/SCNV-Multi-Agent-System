import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "agents"))
from orchestrator import Orchestrator

def main():
    print("Initializing Orchestrator...")
    o = Orchestrator()
    
    print("\n--- Testing SO_CREATED Event (Allocation Efficiency) ---")
    so_event = {
        "event_type": "SO_CREATED",
        "so": {
            "so_number": "4567890001",
            "country_code": "GB",
            "assigned_plant": "GB01"
        }
    }
    
    final_state_so = o.process_event(so_event)
    print("Optimal Plant:", final_state_so.get("optimal_plant"))
    print("Efficiency Score:", final_state_so.get("allocation_efficiency_score"))
    print("Messages:", [m.message_type for m in final_state_so.get("messages", [])])
    
    print("\n--- Testing CRON_DAILY Event (Country KPI) ---")
    cron_event = {
        "event_type": "CRON_DAILY",
        "country_code": "GB"
    }
    
    final_state_cron = o.process_event(cron_event)
    kpis = final_state_cron.get("country_kpi_results")
    if kpis:
        print(f"Total Vol: {kpis.get('total_volume')}")
        print(f"Productive Vol: {kpis.get('productive_volume')}")
        print(f"Productive %: {kpis.get('productive_pct'):.2f}%")
        print("Messages:", [m.message_type for m in final_state_cron.get("messages", [])])

if __name__ == "__main__":
    main()
