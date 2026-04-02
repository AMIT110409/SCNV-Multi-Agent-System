import json
import random
import os
from datetime import datetime, timedelta

def generate_data():
    base_dir = "../data/synthetic"
    out_dir = "../data/synthetic/gap_extended"
    os.makedirs(out_dir, exist_ok=True)
    
    # Load existing data
    with open(os.path.join(base_dir, "plant_master.json"), "r") as f:
        plants = json.load(f)
    
    with open(os.path.join(base_dir, "sku_master.json"), "r") as f:
        skus = json.load(f)
        
    with open(os.path.join(base_dir, "incoming_stos.json"), "r") as f:
        stos = json.load(f)
        
    # 1. Extend Plant Master -> plant_country_master.json
    extended_plants = []
    countries = ["GB", "BE", "DE", "FR", "NL", "US", "IN", "CN"] # Added GB for UK as required
    
    for i, p in enumerate(plants):
        country = p.get("country", "US")
        if country == "nan":
            country = random.choice(countries)
            
        is_strategic = random.choice([True, False])
        ptype = random.choice(["PLANT", "DC", "WAREHOUSE"])
        
        ep = {
            "WERKS": p.get("plant_id")[:4].upper() if p.get("plant_id") else f"P{i:03d}",
            "plant_id": p.get("plant_id"), # keep original reference
            "LAND1": country,
            "PLANT_TYPE": ptype,
            "STRATEGIC_FLAG": "Y" if is_strategic else "N",
            "MAX_CAPACITY_HL": round(random.uniform(50000, 200000), 2),
            "CURRENT_OCCUPANCY_PCT": round(random.uniform(40.0, 95.0), 2)
        }
        extended_plants.append(ep)
        
    plant_dict = {p["plant_id"]: p for p in extended_plants if p.get("plant_id")}
        
    with open(os.path.join(out_dir, "plant_country_master.json"), "w") as f:
        json.dump(extended_plants, f, indent=4)
        
    # 2. Extend SKU Master
    extended_skus = []
    for s in skus:
        es = dict(s)
        sld = es.get("shelf_life_days", random.randint(30, 365))
        es["MIN_FRESHNESS_THRESHOLD"] = int(sld * random.uniform(0.1, 0.3))
        es["SHELF_LIFE_DAYS"] = sld
        extended_skus.append(es)
        
    sku_dict = {s["sku_id"]: s for s in extended_skus}
        
    with open(os.path.join(out_dir, "sku_master_extended.json"), "w") as f:
        json.dump(extended_skus, f, indent=4)
        
    # 3. Extend STOs -> incoming_stos_extended.json
    extended_stos = []
    for s in stos:
        es = dict(s)
        src = es.get("source_location")
        p_info = plant_dict.get(src, {})
        es["COUNTRY_CODE"] = p_info.get("LAND1", "UNKNOWN")
        es["VOLUME_HL"] = round(es.get("quantity", 0) * random.uniform(0.8, 1.2), 2)
        es["movement_type"] = random.choice(["641", "301"])
        es["is_pre_goods_issue"] = random.choice([True, False])
        es["CONFIDENCE_SCORE"] = round(random.uniform(0.5, 0.99), 2)
        extended_stos.append(es)
        
    with open(os.path.join(out_dir, "incoming_stos_extended.json"), "w") as f:
        json.dump(extended_stos, f, indent=4)
        
    # 4. Generate SO Data (customer_orders.json)
    # The doc also mentions "vbak_orders.json, vbap_items.json, likp_deliveries.json" but gives a flat sample schema "customer_orders.json"
    customer_orders = []
    start_date = datetime(2026, 3, 1)
    
    target_countries = ["GB", "BE", "DE"]
    valid_plants_by_country = {c: [p for p in extended_plants if p["LAND1"] == c] for c in target_countries}
    
    for i in range(1, 101):
        country = random.choice(target_countries)
        plants_in_country = valid_plants_by_country.get(country, [])
        if not plants_in_country:
            plants_in_country = extended_plants
            
        assigned_p = random.choice(plants_in_country)
        optimal_p = random.choice(plants_in_country)
        is_optimal = assigned_p["plant_id"] == optimal_p["plant_id"]
        
        eff_score = 1.0 if is_optimal else round(random.uniform(0.4, 0.8), 2)
        
        sku = random.choice(extended_skus)
        
        so_date = start_date + timedelta(days=random.randint(0, 15))
        gi_date = so_date + timedelta(days=random.randint(1, 5))
        
        order = {
            "so_number": f"{45678900 + i:010d}",
            "so_item": f"{10:06d}",
            "customer_number": f"CUST{random.randint(1, 100):03d}",
            "material_number": sku["sku_id"],
            "assigned_plant": assigned_p["WERKS"], # or plant_id
            "optimal_plant": optimal_p["WERKS"],
            "is_optimal_allocation": is_optimal,
            "quantity_hl": round(random.uniform(10.0, 500.0), 2),
            "country_code": country,
            "order_date": so_date.strftime("%Y-%m-%d"),
            "planned_gi_date": gi_date.strftime("%Y-%m-%d"),
            "allocation_efficiency_score": eff_score
        }
        customer_orders.append(order)
        
    with open(os.path.join(out_dir, "customer_orders.json"), "w") as f:
        json.dump(customer_orders, f, indent=4)
        
    print(f"Successfully generated extended synthetic data in {out_dir}")

if __name__ == "__main__":
    generate_data()
