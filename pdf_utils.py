from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract plain text from all pages of a PDF using pypdf.
    Returns a single string with page contents separated by blank lines.
    """
    reader = PdfReader(str(pdf_path))
    parts: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        cleaned = text.strip()
        if cleaned:
            parts.append(cleaned)
    return "\n\n".join(parts).strip()


print(extract_pdf_text(Path(__file__).parent / "grant_files" / "second_generated_grant.pdf"))



