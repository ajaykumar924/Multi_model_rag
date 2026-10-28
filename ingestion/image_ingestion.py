import base64
import io
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Union

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from langchain_core.documents import Document

load_dotenv()

logger = logging.getLogger(__name__)

# Global EasyOCR reader cache
_easyocr_reader = None


def get_image_mime_type(path: Path) -> str:
    """Return appropriate MIME type based on file extension."""
    suffix = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".gif": "image/gif",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }
    return mime_map.get(suffix, "image/jpeg")


def configure_tesseract() -> bool:
    """Ensure Tesseract executable path is set on Windows or PATH."""
    try:
        if shutil.which("tesseract"):
            return True

        standard_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        ]

        for p in standard_paths:
            candidate = Path(p)
            if candidate.exists():
                pytesseract.pytesseract.tesseract_cmd = str(candidate)
                return True

        return False
    except Exception as e:
        logger.debug(f"Tesseract config check: {e}")
        return False


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Enhance image for OCR engines (adaptive upscaling, contrast, sharpening)."""
    # 1. Upscale if image resolution is low (< 1200px) so characters have adequate pixel height
    w, h = image.size
    min_dim = min(w, h)
    if min_dim < 1200:
        scale = max(2, min(4, int(1600 / max(min_dim, 1))))
        image = image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

    # 2. Convert to grayscale for cleaner thresholding
    if image.mode != "L":
        image = image.convert("L")

    # 3. Enhance contrast to separate foreground text from background
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.8)

    # 4. Sharpen edges of characters
    image = image.filter(ImageFilter.SHARPEN)

    return image


def extract_with_vision(image_input: Union[Path, str, Image.Image]) -> str:
    """Extract structured text, diagrams, and layout using OpenAI Vision (GPT-4o / GPT-4o-mini)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.info("OPENAI_API_KEY not configured, skipping Vision AI.")
        return ""

    try:
        client = OpenAI(api_key=api_key)

        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            mime_type = get_image_mime_type(path)
            with open(path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
        else:
            # PIL Image
            mime_type = "image/png"
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        prompt = (
            "Extract all text, headings, numbers, diagrams, tables, and notes from this image accurately. "
            "Preserve layout hierarchy using Markdown headings and bullet points. "
            "Format tabular data as Markdown tables. "
            "For infographics or multi-column layouts, extract section by section in logical reading order. "
            "Do not omit any text, labels, or captions."
        )

        model = os.getenv("VISION_MODEL") or os.getenv("LLM_MODEL", "gpt-4o-mini")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=2000,
            temperature=0.0,
        )

        result = response.choices[0].message.content.strip()
        if result:
            logger.info("Vision AI extracted text successfully.")
            return result
        return ""

    except Exception as e:
        logger.warning(f"Vision extraction failed: {e}")
        return ""


def get_easyocr_reader():
    """Lazy initialize and cache EasyOCR reader instance."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            import torch

            use_gpu = torch.cuda.is_available()
            # Set verbose=False to prevent UnicodeEncodeError on Windows terminals
            _easyocr_reader = easyocr.Reader(["en"], gpu=use_gpu, verbose=False)
            logger.info("EasyOCR initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}")
            _easyocr_reader = False

    return _easyocr_reader if _easyocr_reader is not False else None


def extract_with_easyocr(image_input: Union[Path, str, Image.Image]) -> str:
    """Extract text using open-source deep learning OCR (EasyOCR) with paragraph grouping."""
    reader = get_easyocr_reader()
    if not reader:
        return ""

    try:
        # Load as PIL Image to allow preprocessing & upscaling
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(str(image_input))
        else:
            pil_img = image_input

        # Upscale low-res images for better recognition
        w, h = pil_img.size
        if min(w, h) < 1000:
            scale = max(2, min(4, int(1500 / max(min(w, h), 1))))
            pil_img = pil_img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

        # Convert to numpy array for EasyOCR
        import numpy as np

        img_np = np.array(pil_img)

        # Use paragraph=True to group words into cohesive sentences and avoid split lines
        results = reader.readtext(img_np, paragraph=True)

        paragraphs = []
        for item in results:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                text = str(item[1]).strip()
                if text:
                    paragraphs.append(text)

        extracted = "\n\n".join(paragraphs).strip()
        if extracted:
            logger.info("EasyOCR extracted text successfully.")
            return extracted
        return ""

    except Exception as e:
        logger.warning(f"EasyOCR extraction failed: {e}")
        return ""


def extract_with_tesseract(image_input: Union[Path, str, Image.Image]) -> str:
    """Extract text using Tesseract OCR with adaptive image preprocessing."""
    configure_tesseract()

    try:
        if isinstance(image_input, (str, Path)):
            image = Image.open(str(image_input))
        else:
            image = image_input

        # Apply multi-stage preprocessing
        processed = preprocess_for_ocr(image)

        # Try automatic page segmentation (PSM 3)
        text = pytesseract.image_to_string(processed, config="--psm 3").strip()

        # If too little text was detected, try single uniform block (PSM 6)
        if len(text) < 30:
            alt_text = pytesseract.image_to_string(processed, config="--psm 6").strip()
            if len(alt_text) > len(text):
                text = alt_text

        return text.strip()

    except Exception as e:
        logger.warning(f"Tesseract OCR failed: {e}")
        return ""


def extract_text_from_image(image_input: Union[Path, str, Image.Image]) -> Tuple[str, str]:
    """
    Multi-tier extraction strategy:
    1. Vision AI (OpenAI GPT-4o-mini / Vision) for optimal layout and diagram comprehension.
    2. Open-source Deep Learning OCR (EasyOCR) with spatial paragraph detection.
    3. Open-source Tesseract OCR with adaptive preprocessing as reliable fallback.
    """
    # 1. Try Vision AI
    text = extract_with_vision(image_input)
    if text:
        return text, "vision_ai"

    # 2. Try Open-Source EasyOCR
    text = extract_with_easyocr(image_input)
    if text:
        return text, "easyocr"

    # 3. Fallback to preprocessed Tesseract OCR
    text = extract_with_tesseract(image_input)
    if text:
        return text, "tesseract_ocr"

    return "", "none"


def load_image(file_path: str) -> list[Document]:
    """Extract text from an image using multi-tier AI vision and open-source OCR."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    text, method = extract_text_from_image(path)

    fallback_content = (
        f"Image file: {path.name}. "
        "No readable text was detected by Vision AI or OCR."
    )

    return [
        Document(
            page_content=text or fallback_content,
            metadata={
                "source": path.name,
                "file_type": "image",
                "image_path": str(path.resolve()),
                "has_ocr_text": bool(text),
                "extraction_method": method,
            },
        )
    ]
