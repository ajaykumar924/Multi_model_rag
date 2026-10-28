
from pathlib import Path
from langchain_community.document_loaders import CSVLoader


def load_csv(file_path: str):
    """Load CSV rows into LangChain Documents."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    loader = CSVLoader(
        file_path=str(path),
        encoding="utf-8",
    )

    documents = loader.load()

    for doc in documents:
        doc.metadata["source"] = path.name
        doc.metadata["file_type"] = "csv"

    return documents
