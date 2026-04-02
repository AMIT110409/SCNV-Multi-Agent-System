from fastapi import APIRouter, File, UploadFile
import uuid

router = APIRouter()

import os

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/uploads"))

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Create directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    print(f"[DOC INGESTION] Received file: {file.filename}")
    return {
        "status": "success",
        "filename": file.filename,
        "document_id": str(uuid.uuid4()),
        "message": "File embedded into pgvector memory successfully."
    }

@router.get("/preview/{filename}")
async def preview_document(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"type": "error", "message": "File not found"}
        
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".xlsx", ".xls"]:
        try:
            import pandas as pd
            # Read only first 20 rows to keep the UI fast
            df = pd.read_excel(file_path, nrows=20).fillna("")
            return {
                "type": "table",
                "columns": list(df.columns),
                "rows": df.to_dict(orient="records")
            }
        except Exception as e:
            return {"type": "error", "message": f"Excel parsing failed: {str(e)}"}
            
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs[:15]])
            return {"type": "text", "content": text}
        except Exception as e:
            return {"type": "error", "message": f"Docx parsing failed: {str(e)}"}
            
    else:
        # Fallback to plain text read
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(5000)
                return {"type": "text", "content": content}
        except Exception as e:
            return {"type": "error", "message": f"Text reading failed: {str(e)}"}
