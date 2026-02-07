"""Test PDF extraction — both regular and scanned."""

from pathlib import Path
from app.utils.pdf_parser import extract_text_from_pdf

# --- Test 1: Regular PDF ---
# We'll create a simple PDF with actual text using PyMuPDF
import fitz

print("=" * 60)
print("TEST 1: Regular PDF (direct text extraction)")
print("=" * 60)

# Create a regular PDF with text
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 100), "This is a regular PDF with real text.", fontsize=14)
page.insert_text((50, 130), "The refund policy allows returns within 30 days.", fontsize=14)
page.insert_text((50, 160), "Employees receive 20 days of paid time off.", fontsize=14)
doc.save("test_regular.pdf")
doc.close()

text = extract_text_from_pdf(Path("test_regular.pdf"))
print(f"\nExtracted text:\n{text}\n")


# --- Test 2: Scanned PDF ---
# We'll create an image-only PDF (simulating a scanned document)
print("=" * 60)
print("TEST 2: Scanned PDF (OCR extraction)")
print("=" * 60)

from PIL import Image, ImageDraw, ImageFont

# Create an image with text (like a scanned document)
img = Image.new("RGB", (800, 200), color="white")
draw = ImageDraw.Draw(img)
draw.text((50, 30), "This is a scanned document.", fill="black")
draw.text((50, 70), "It has no real text data inside the PDF.", fill="black")
draw.text((50, 110), "OCR is needed to read this page.", fill="black")

# Save the image as a PDF (no text layer, just pixels)
img.save("test_scanned.pdf", "PDF")

text = extract_text_from_pdf(Path("test_scanned.pdf"))
print(f"\nExtracted text:\n{text}\n")


# Cleanup
Path("test_regular.pdf").unlink()
Path("test_scanned.pdf").unlink()
print("✅ Both tests complete! Temp files cleaned up.")