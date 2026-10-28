
from pathlib import Path
import pymupdf
import pytesseract
from PIL import Image
from io import BytesIO
from langchain_core.documents import Document
from ingestion.image_ingestion import extract_text_from_image


def load_pdf(file_path: str):
    """Extract PDF text and OCR scanned pages when needed."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    documents = []

    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):

            text = page.get_text("text").strip()

            # OCR pages that contain little selectable text.
            if len(text) < 30:
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False,
                )

                image = Image.open(
                    BytesIO(pixmap.tobytes("png"))
                )

                ocr_text, method = extract_text_from_image(image)
                if ocr_text:
                    text = ocr_text

            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": path.name,
                            "file_type": "pdf",
                            "page_number": page_number,
                        },
                    )
                )

    return documents
