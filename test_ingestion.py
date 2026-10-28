
from pathlib import Path

from ingestion.word_ingestion import load_word
from ingestion.csv_ingestion import load_csv
from ingestion.excel_ingestion import load_excel
from ingestion.pdf_ingestion import load_pdf
from ingestion.image_ingestion import load_image


DATA_DIR = Path("data")

LOADERS = {
    ".pdf": load_pdf,
    ".csv": load_csv,
    ".docx": load_word,
    ".xlsx": load_excel,
    ".png": load_image,
    ".jpg": load_image,
    ".jpeg": load_image,
    ".webp": load_image,
    ".tif": load_image,
    ".tiff": load_image,
    ".bmp": load_image,
}


def test_ingestion():
    if not DATA_DIR.exists():
        print("ERROR: data folder not found.")
        return

    files = [
        path for path in DATA_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in LOADERS
    ]

    if not files:
        print("No supported files found in data/.")
        return

    for path in files:
        print(f"\nProcessing: {path}")

        try:
            loader = LOADERS[path.suffix.lower()]
            documents = loader(str(path))

            print(f"Documents extracted: {len(documents)}")

            for doc in documents[:2]:
                print("Metadata:", doc.metadata)
                print("Text preview:", doc.page_content[:300])

        except Exception as error:
            print(f"FAILED: {path.name}")
            print(error)


if __name__ == "__main__":
    test_ingestion()
