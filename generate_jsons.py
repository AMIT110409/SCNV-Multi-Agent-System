import pandas as pd
import json
import os
import random

data_dir = r"c:\Users\Abcom\Downloads\scnv-agent\data\raw_tables"
out_dir = r"c:\Users\Abcom\Downloads\scnv-agent\data\synthetic"
os.makedirs(out_dir, exist_ok=True)

print("Loading CSV files...")

# Load DataFrames
t001w = pd.read_csv(f"{data_dir}\\T001W.csv")
kna1 = pd.read_csv(f"{data_dir}\\KNA1.csv")
mara = pd.read_csv(f"{data_dir}\\MARA.csv")
marc = pd.read_csv(f"{data_dir}\\MARC.csv")
likp = pd.read_csv(f"{data_dir}\\LIKP.csv")
lips = pd.read_csv(f"{data_dir}\\LIPS.csv")

# 1. plant_master.json
print("Generating plant_master.json...")
plants = []
for _, row in t001w.drop_duplicates(subset=['Plant']).iterrows():
    plants.append({
        "plant_id": str(row.get('Plant', '')),
        "country": str(row.get('Country', '')),
        "region": str(row.get('Region', ''))
    })
with open(f"{out_dir}\\plant_master.json", "w") as f:
    json.dump(plants, f, indent=4)

# 2. dc_master.json
print("Generating dc_master.json...")
dcs = []
for _, row in kna1.drop_duplicates(subset=['Customer']).iterrows():
    dcs.append({
        "dc_id": str(row.get('Customer', '')),
        "name": str(row.get('Name', '')),
        "country": str(row.get('Country', ''))
    })
# Let's also treat some plants as DCs to make the network interesting if KNA1 is small
plant_dcs = []
for _, row in t001w.sample(min(10, len(t001w))).iterrows():
    plant_dcs.append({
        "dc_id": f"DC_{row.get('Plant', '')}",
        "name": f"Distribution Center {row.get('Plant', '')}",
        "country": str(row.get('Country', ''))
    })

all_dcs = dcs + plant_dcs
with open(f"{out_dir}\\dc_master.json", "w") as f:
    json.dump(all_dcs, f, indent=4)

# 3. sku_master.json
print("Generating sku_master.json...")
sku_counts = marc.groupby('MaterialNumber')['Plant'].nunique()
# Let's take a sample of 100 SKUs to keep the JSON manageable, or take all if we want
sampled_skus = mara.sample(min(500, len(mara)))

skus = []
for _, row in sampled_skus.iterrows():
    matnr = row['MaterialNumber']
    count = sku_counts.get(matnr, 0)
    source_model = "DUAL" if count > 1 else "SINGLE"
    sourcing_plants = list(marc[marc['MaterialNumber'] == matnr]['Plant'].unique())
    skus.append({
        "sku_id": str(matnr),
        "material_type": str(row.get('MaterialType', '')),
        "source_model": source_model,
        "sourcing_plants": [str(p) for p in sourcing_plants],
        "shelf_life_days": random.randint(30, 365) # Mocked shelf life
    })
with open(f"{out_dir}\\sku_master.json", "w") as f:
    json.dump(skus, f, indent=4)

# 4. incoming_stos.json
print("Generating incoming_stos.json...")
# Join LIKP and LIPS to get full STO picture
# Limit to 500 for the MVP demo as per the requirements
stos_merged = pd.merge(lips, likp[['DocumentNumber', 'Customer']], on='DocumentNumber', how='inner')
stos_sample = stos_merged.sample(min(500, len(stos_merged)))

stos = []
sto_id_counter = 100000
valid_plant_ids = set([p['plant_id'] for p in plants])
valid_dc_ids = set([d['dc_id'] for d in all_dcs])

for _, row in stos_sample.iterrows():
    source_plant = str(row.get('Plant', ''))
    dest = str(row.get('Customer', ''))
    if pd.isna(source_plant) or not source_plant:
        # If no plant, randomly assign one from our master for the demo
        source_plant = random.choice(list(valid_plant_ids)) if valid_plant_ids else "P1"
        
    if pd.isna(dest) or not dest:
        dest = random.choice(list(valid_dc_ids)) if valid_dc_ids else "DC1"

    stos.append({
        "sto_id": f"STO_{sto_id_counter}",
        "source_location": source_plant,
        "destination_location": dest,
        "sku_id": str(row.get('MaterialNumber', '')),
        "quantity": float(row.get('DeliveryQuantity', 0.0)),
        "creation_date": "2026-03-14T00:00:00Z"
    })
    sto_id_counter += 1

with open(f"{out_dir}\\incoming_stos.json", "w") as f:
    json.dump(stos, f, indent=4)

# 5. strategic_matrix.json
print("Generating strategic_matrix.json...")
matrix = []
# Create a matrix for connections between our sources and destinations
for source in list(valid_plant_ids)[:10]: # Pick a few sources
    for dc in list(valid_dc_ids)[:5]: # Pick a few DCs
        matrix.append({
            "source": source,
            "destination": dc,
            "is_strategic_lane": random.choice([True, False]),
            "capacity_utilization": random.uniform(0.4, 0.95)
        })

with open(f"{out_dir}\\strategic_matrix.json", "w") as f:
    json.dump(matrix, f, indent=4)

print("Successfully generated all 5 JSON files in data/synthetic/")
