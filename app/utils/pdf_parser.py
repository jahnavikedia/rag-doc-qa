"""PDF text extraction — supports both regular and scanned PDFs."""

from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file.

    First tries direct text extraction (fast, works for regular PDFs).
    If no text is found, falls back to OCR (slower, works for scanned PDFs).

    Args:
        file_path: Path to the PDF file.

    Returns:
        The full text content of the PDF.

    Raises:
        ValueError: If the PDF can't be opened or has no extractable text.
    """
    try:
        doc = fitz.open(str(file_path))
    except Exception as exc:
        raise ValueError(f"Could not open PDF: {exc}") from exc

    pages: list[str] = []
    ocr_used = False

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Try direct text extraction first (fast)
        text = page.get_text("text").strip()

        if text:
            pages.append(text)
        else:
            # No text found — this page is probably a scanned image
            # Fall back to OCR
            ocr_text = _ocr_page(page)
            if ocr_text:
                pages.append(ocr_text)
                ocr_used = True

    doc.close()

    if not pages:
        raise ValueError(
            "No extractable text found in PDF. "
            "Neither direct extraction nor OCR produced results."
        )

    full_text = "\n\n".join(pages)

    method = "OCR" if ocr_used else "direct"
    print(f"📄 Extracted {len(pages)} pages ({method}), {len(full_text)} characters")

    return full_text


def _ocr_page(page: fitz.Page) -> str:
    """Run OCR on a single PDF page.

    Renders the page as a high-resolution image,
    then uses Tesseract to extract text from it.

    Args:
        page: A PyMuPDF page object.

    Returns:
        Extracted text, or empty string if OCR fails.
    """
    try:
        # Render page as image (2x zoom for better OCR accuracy)
        zoom = 2.0
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)

        # Convert to PIL Image
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))

        # Run OCR
        text = pytesseract.image_to_string(image).strip()
        return text

    except Exception as exc:
        print(f"⚠️  OCR failed on page {page.number}: {exc}")
        return ""