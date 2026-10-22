
from io import BytesIO
import pytest
from pypdf import PdfWriter
from app.tools import extract_pdf_text


def test_extract_pdf_rejects_empty_bytes():
    with pytest.raises(ValueError, match="empty"):
        extract_pdf_text(b"")


def test_extract_pdf_rejects_pdf_without_text():
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.write(buffer)

    with pytest.raises(ValueError, match="OCR"):
        extract_pdf_text(buffer.getvalue())
