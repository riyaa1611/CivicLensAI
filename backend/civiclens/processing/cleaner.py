"""Text cleaning utilities for raw scraped policy content."""
import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean raw scraped or extracted text:
    - Normalize unicode
    - Remove excessive whitespace
    - Strip HTML artifacts
    - Remove null bytes
    """
    if not text:
        return ""

    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)

    # Remove null bytes and control characters (keep newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Remove HTML entities
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)

    # Remove URLs (but keep domain hints for context)
    text = re.sub(r"https?://\S+", "", text)

    # Collapse multiple spaces within lines
    text = re.sub(r" {2,}", " ", text)

    # Collapse multiple blank lines into two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.splitlines()]

    # Remove very short lines that are likely noise (page numbers, etc.)
    lines = [line for line in lines if len(line) > 2 or line == ""]

    return "\n".join(lines).strip()


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF (fitz).
    Falls back to PyPDF2 if fitz is unavailable.
    """
    # Try PyMuPDF first (better quality)
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return clean_text("\n\n".join(pages))
    except ImportError:
        pass

    # Fallback to PyPDF2
    try:
        import io
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return clean_text("\n\n".join(pages))
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {e}") from e
