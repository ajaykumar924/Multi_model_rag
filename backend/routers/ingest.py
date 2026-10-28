import hashlib
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingestion.csv_ingestion import load_csv
from ingestion.excel_ingestion import load_excel
from ingestion.image_ingestion import load_image
from ingestion.pdf_ingestion import load_pdf
from ingestion.word_ingestion import load_word
from vector_store.postgres_store import delete_documents_by_source, get_text_store

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Ingestion"])

UPLOAD_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "uploads"
)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".csv", ".xlsx", ".docx",
    ".png", ".jpg", ".jpeg", ".webp",
    ".tif", ".tiff", ".bmp",
}


def load_uploaded_file(path: Path):
    extension = path.suffix.lower()

    if extension == ".pdf":
        return load_pdf(str(path))
    elif extension == ".csv":
        return load_csv(str(path))
    elif extension == ".xlsx":
        return load_excel(str(path))
    elif extension == ".docx":
        return load_word(str(path))
    else:
        return load_image(str(path))


@router.post("/ingest")
def ingest_documents():
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Find supported uploaded files
        files = [
            path for path in UPLOAD_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not files:
            raise HTTPException(
                status_code=400,
                detail="No supported uploaded files found in data/uploads/."
            )

        # 2. Load the files
        documents = []

        for path in files:
            logger.info(f"Loading uploaded file: {path.name}")
            print(f"Loading: {path.name}")
            documents.extend(load_uploaded_file(path))

        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the uploaded files."
            )

        # 3. Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True,
        )

        chunks = splitter.split_documents(documents)

        # 4. Clean previous chunks for files being re-ingested
        sources_to_clean = {
            chunk.metadata.get("source") for chunk in chunks
            if chunk.metadata.get("source")
        }
        for src in sources_to_clean:
            deleted_count = delete_documents_by_source(src)
            if deleted_count:
                logger.info(f"Cleaned {deleted_count} stale chunk(s) for '{src}'.")

        # 5. Generate unique IDs for every chunk
        ids = []
        seen_ids = set()

        for index, chunk in enumerate(chunks):
            source = chunk.metadata.get("source", "unknown")
            start_index = chunk.metadata.get("start_index", index)

            unique_text = f"{source}|{start_index}|{chunk.page_content}"
            base_id = hashlib.sha256(unique_text.encode("utf-8")).hexdigest()

            chunk_id = base_id
            duplicate_number = 1

            while chunk_id in seen_ids:
                chunk_id = f"{base_id}_{duplicate_number}"
                duplicate_number += 1

            seen_ids.add(chunk_id)
            ids.append(chunk_id)

        # 6. Save to PostgreSQL / pgvector
        store = get_text_store()
        store.add_documents(chunks, ids=ids)

        return {
            "message": "Ingestion completed successfully.",
            "files_processed": len(files),
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "files": [path.name for path in files],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ingestion failed")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )
