
from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader


def load_word(file_path: str):
    """Load a Word document into LangChain Documents."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    loader = Docx2txtLoader(str(path))
    documents = loader.load()

    for doc in documents:
        doc.metadata["source"] = path.name
        doc.metadata["file_type"] = "word"

    return documents
