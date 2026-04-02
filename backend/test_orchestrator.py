import sys
import os

agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../agents"))
sys.path.append(agents_dir)

try:
    from orchestrator import Orchestrator
    o = Orchestrator()
    dummy_sto = {
        "sto_id": "MSG-123",
        "source_location": "DC_North",
        "destination_location": "Store_44",
        "sku_id": "Laptops-X1",
        "quantity": 50
    }
    print("Testing orchestrator...")
    res = o.process_sto_event(dummy_sto)
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
