import argparse
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingestion.csv_ingestion import load_csv
from ingestion.excel_ingestion import load_excel
from ingestion.image_ingestion import load_image
from ingestion.pdf_ingestion import load_pdf
from ingestion.word_ingestion import load_word
from vector_store.postgres_store import delete_documents_by_source, get_text_store

load_dotenv()

DATA_DIR = Path("data")

SUPPORTED_EXTENSIONS = {
    ".pdf", ".csv", ".xlsx", ".docx",
    ".png", ".jpg", ".jpeg", ".webp",
    ".tif", ".tiff", ".bmp",
}


def load_single_file(path: Path) -> list:
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


def load_all_documents(target_file: str = None):
    documents = []

    if target_file:
        file_path = Path(target_file)
        if not file_path.is_file():
            print(f"Error: file not found: {target_file}")
            return []
        print(f"Loading single file: {file_path.name}")
        return load_single_file(file_path)

    for path in DATA_DIR.rglob("*"):
        if not path.is_file():
            continue

        extension = path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        print("Loading:", path.name)
        documents.extend(load_single_file(path))

    return documents


def ingest_documents(documents):
    if not documents:
        print("No documents found.")
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)
    print("Chunks created:", len(chunks))

    # Clean previous chunks for the sources being ingested to prevent stale/corrupt data
    sources_to_update = {
        chunk.metadata.get("source") for chunk in chunks
        if chunk.metadata.get("source")
    }
    for src in sources_to_update:
        deleted = delete_documents_by_source(src)
        if deleted:
            print(f"Cleaned {deleted} stale chunk(s) for '{src}'.")

    # Generate unique, stable IDs for every chunk
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

    store = get_text_store()
    store.add_documents(chunks, ids=ids)

    print("Ingestion completed successfully!")
    print("Chunks submitted to PostgreSQL:", len(chunks))
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into PostgreSQL vector store")
    parser.add_argument("--file", "-f", type=str, help="Ingest a specific file instead of all files")
    args = parser.parse_args()

    documents = load_all_documents(target_file=args.file)
    print(f"\nDocuments loaded: {len(documents)}")
    ingest_documents(documents)


if __name__ == "__main__":
    main()
