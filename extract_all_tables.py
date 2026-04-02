import pandas as pd
import os

file_path = r'c:\Users\Abcom\Downloads\scnv-agent\docs\SCNV Data.xlsx'
output_dir = r'c:\Users\Abcom\Downloads\scnv-agent\data\raw_tables'

os.makedirs(output_dir, exist_ok=True)

print(f"Loading {file_path} (this may take a minute due to 235MB size)...")
try:
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    print(f"Found {len(sheets)} sheets. Starting extraction to {output_dir}...")
    
    for sheet in sheets:
        print(f"Extracting sheet: {sheet}...")
        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            output_file = os.path.join(output_dir, f"{sheet}.csv")
            df.to_csv(output_file, index=False)
            print(f"  -> Saved {output_file} ({len(df)} rows)")
        except Exception as e:
            print(f"  -> Error extracting sheet {sheet}: {e}")
            
    print("All extraction complete.")
except Exception as e:
    print(f"Fatal error: {e}")
