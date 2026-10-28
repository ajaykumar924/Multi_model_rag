#test for recursive chunking

from pathlib import Path

from ingestion.word_ingestion import load_word
from ingestion.csv_ingestion import load_csv
from ingestion.excel_ingestion import load_excel
from ingestion.pdf_ingestion import load_pdf
from ingestion.image_ingestion import load_image

from chunking.recursive_chunking import recursive_chunking


DATA_DIR = Path("data")

LOADERS = {
    ".pdf": load_pdf,
    ".csv": load_csv,
    ".docx": load_word,
    ".xlsx": load_excel,
    ".png": load_image,
    ".jpg": load_image,
    ".jpeg": load_image,
    ".tif": load_image,
    ".tiff": load_image,
    ".bmp": load_image,
}


def test_recursive_chunking():
    all_documents = []

    for path in DATA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in LOADERS:
            print(f"Loading: {path.name}")

            loader = LOADERS[path.suffix.lower()]
            documents = loader(str(path))

            all_documents.extend(documents)

    print(f"\nTotal documents loaded: {len(all_documents)}")

    chunks = recursive_chunking(all_documents)

    print(f"Total chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Chunk {i} ---")
        print("Metadata:", chunk.metadata)
        print("Content:", chunk.page_content[:300])


if __name__ == "__main__":
    test_recursive_chunking()


#testing row based chunking 


from pathlib import Path

from ingestion.csv_ingestion import load_csv
from ingestion.excel_ingestion import load_excel
from chunking.row_chunking import row_chunking


DATA_DIR = Path("data")

LOADERS = {
    ".csv": load_csv,
    ".xlsx": load_excel,
}


def test_row_chunking():
    all_documents = []

    for path in DATA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in LOADERS:
            print(f"\nLoading: {path.name}")

            documents = LOADERS[path.suffix.lower()](str(path))
            all_documents.extend(documents)

            print(f"Rows/documents loaded: {len(documents)}")

    chunks = row_chunking(all_documents)

    print(f"\nTotal documents loaded: {len(all_documents)}")
    print(f"Total row chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Row chunk {i} ---")
        print("Metadata:", chunk.metadata)
        print("Content:", chunk.page_content[:300])


if __name__ == "__main__":
    test_row_chunking()


#test image chunking 


from pathlib import Path

from ingestion.image_ingestion import load_image
from chunking.image_chunking import image_chunking


DATA_DIR = Path("data")

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"
}


def test_image_chunking():
    image_documents = []

    for path in DATA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            print(f"\nLoading image: {path.name}")

            documents = load_image(str(path))
            image_documents.extend(documents)

    print(f"\nImage documents loaded: {len(image_documents)}")

    image_chunks = image_chunking(image_documents)

    print(f"Image chunks created: {len(image_chunks)}")

    for i, doc in enumerate(image_chunks[:3], start=1):
        print(f"\n--- Image {i} ---")
        print("Metadata:", doc.metadata)
        print("Content:", doc.page_content[:300])


if __name__ == "__main__":
    test_image_chunking()
    


# test semantic chunking 


import os
from pathlib import Path
from dotenv import load_dotenv

from ingestion.word_ingestion import load_word
from ingestion.pdf_ingestion import load_pdf
from chunking.semantic_chunking import semantic_chunking

load_dotenv()

DATA_DIR = Path("data")

LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_word,
}


def test_semantic_chunking():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env")
        return

    all_documents = []

    for path in DATA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in LOADERS:
            print(f"Loading: {path.name}")

            documents = LOADERS[path.suffix.lower()](str(path))
            all_documents.extend(documents)

    print(f"\nDocuments loaded: {len(all_documents)}")

    # Test on a small sample first to limit API usage.
    sample_documents = all_documents[:3]

    print(f"Documents sent for semantic chunking: {len(sample_documents)}")

    chunks = semantic_chunking(sample_documents)

    print(f"Semantic chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Semantic Chunk {i} ---")
        print("Metadata:", chunk.metadata)
        print("Content:", chunk.page_content[:300])


if __name__ == "__main__":
    test_semantic_chunking()
