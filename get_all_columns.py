import pandas as pd
import glob

data_dir = r"c:\Users\Abcom\Downloads\scnv-agent\data\raw_tables"
csv_files = glob.glob(f"{data_dir}\\*.csv")

unique_columns = set()

for file in csv_files:
    try:
        df = pd.read_csv(file, nrows=0) # Just read headers
        unique_columns.update(df.columns)
    except Exception as e:
        print(f"Error reading {file}: {e}")

print("Unique columns across all files:")
for col in sorted(unique_columns):
    print(col)
