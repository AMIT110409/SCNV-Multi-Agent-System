import pandas as pd
import json

data_dir = r"c:\Users\Abcom\Downloads\scnv-agent\data\raw_tables"
expected_files = ["LIKP.csv", "LIPS.csv"]

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

report.append("--- Validating STO Data Sources against SCNV Architecture ---")

check_file("LIKP.csv", ["Vbeln", "Lfart", "Kunnr"]) # LIKP: Delivery Header (Kunnr = Customer/Destination)
check_file("LIPS.csv", ["Vbeln", "Posnr", "Matnr", "Werks", "Lfimg"]) # LIPS: Delivery Item (Matnr = SKU, Werks = Source Plant, Lfimg = Quantity)


with open("validation_report_sto.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("Validation script complete.")
