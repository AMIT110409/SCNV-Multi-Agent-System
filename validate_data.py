import pandas as pd
import json

data_dir = r"c:\Users\Abcom\Downloads\scnv-agent\data\raw_tables"
expected_files = ["EKKO.csv", "EKPO.csv", "T001W.csv", "T001.csv", "KNA1.csv", "MARA.csv", "MARC.csv"]

report = []

def check_file(filename, required_cols):
    filepath = f"{data_dir}\\{filename}"
    try:
        df = pd.read_csv(filepath, nrows=5)
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            report.append(f"❌ {filename} is MISSING expected columns: {missing_cols}")
            report.append(f"   Available columns: {list(df.columns)}")
        else:
            report.append(f"✅ {filename} has all required columns: {required_cols}")
    except Exception as e:
        report.append(f"❌ Error reading {filename}: {e}")

report.append("--- Validating Data Sources against SCNV Architecture ---")

# 1. plant_master.json (needs Plant IDs and Names from T001W/T001)
report.append("\n1. plant_master.json")
check_file("T001W.csv", ["Werks", "Land1", "Regio"]) 
# T001W provides Plant ID (Werks), Country (Land1). We'll also need Names, which might be in another table, or we can use IDs.

# 2. dc_master.json (needs DC IDs from KNA1 or T001W)
report.append("\n2. dc_master.json")
check_file("KNA1.csv", ["Kunnr", "Land1", "Name1"])

# 3. sku_master.json (needs SKUs from MARA, and sourcing plant links from MARC)
report.append("\n3. sku_master.json")
check_file("MARA.csv", ["Matnr", "Mtart", "Meins"])
check_file("MARC.csv", ["Matnr", "Werks"])

# 4. incoming_stos.json (needs Purchase Orders with supplying/receiving plants)
report.append("\n4. incoming_stos.json")
check_file("EKKO.csv", ["Ebeln", "Bedat"]) # Usually EKKO has Reswk (Supplying Plant), let's check what it has.
check_file("EKPO.csv", ["Ebeln", "Ebelp", "Matnr", "Werks", "Menge"]) # EKPO has Receiving Plant (Werks) usually, Matnr (SKU).

with open("validation_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("Validation script complete.")
