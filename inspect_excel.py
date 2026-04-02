import pandas as pd

file_path = r'c:\Users\Abcom\Downloads\scnv-agent\docs\SCNV Data.xlsx'
print(f"Loading {file_path}...")
try:
    xl = pd.ExcelFile(file_path)
    print("Sheets:", xl.sheet_names)
    
    with open('data_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f"Sheets in {file_path}:\n")
        f.write(str(xl.sheet_names) + "\n\n")
        for sheet in xl.sheet_names:
            f.write(f"--- Sheet: {sheet} ---\n")
            try:
                df = pd.read_excel(xl, sheet_name=sheet, nrows=5)
                f.write(f"Columns: {list(df.columns)}\n")
                f.write("Sample data:\n")
                f.write(df.to_string() + "\n\n")
                print(f"Processed sheet: {sheet}")
            except Exception as e:
                f.write(f"Error reading sheet: {e}\n\n")
                print(f"Error reading sheet {sheet}: {e}")
    print("Finished writing to data_summary.txt")
except Exception as e:
    print(f"Fatal error: {e}")
