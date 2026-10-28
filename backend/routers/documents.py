from pathlib import Path
import os
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from dotenv import load_dotenv

from vector_store.postgres_store import delete_documents_by_source

load_dotenv()

router = APIRouter(prefix="/api", tags=["Documents"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc",
    ".xlsx", ".xls", ".csv",
    ".txt", ".md",
    ".jpg", ".jpeg", ".png", ".webp",
    ".tif", ".tiff", ".bmp",
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".tif", ".tiff", ".bmp",
}


@router.get("/documents")
def list_documents():
    """List all uploaded documents."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    docs = []
    for p in UPLOAD_DIR.iterdir():
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS:
            size_kb = round(p.stat().st_size / 1024, 1)
            docs.append({
                "filename": p.name,
                "size_kb": size_kb,
                "extension": p.suffix.lower(),
                "is_image": p.suffix.lower() in IMAGE_EXTENSIONS,
                "modified": p.stat().st_mtime,
            })
    return {"documents": docs}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), overwrite: bool = Query(True)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}",
        )

    destination = UPLOAD_DIR / filename

    if destination.exists() and not overwrite:
        raise HTTPException(
            status_code=409,
            detail="A file with this name already exists.",
        )

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                output.write(chunk)

        is_image = extension in IMAGE_EXTENSIONS

        return {
            "message": f"File '{filename}' uploaded successfully.",
            "filename": filename,
            "saved_to": str(destination),
            "is_image": is_image,
        }

    except Exception as e:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Could not save the uploaded file: {str(e)}",
        )

    finally:
        await file.close()


@router.delete("/documents/{filename}")
def delete_document(filename: str):
    """Delete a document file and remove its vector embeddings."""
    safe_filename = Path(filename).name
    target = UPLOAD_DIR / safe_filename

    deleted_file = False
    if target.exists() and target.is_file():
        target.unlink()
        deleted_file = True

    # Also remove from vector database
    deleted_chunks = delete_documents_by_source(safe_filename)

    if not deleted_file and deleted_chunks == 0:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "message": f"Document '{safe_filename}' deleted.",
        "file_deleted": deleted_file,
        "chunks_removed": deleted_chunks,
    }
