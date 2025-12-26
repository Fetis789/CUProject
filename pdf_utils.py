from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path, type: str = "application") -> str:
    """
    Extract plain text from all pages of a PDF using pypdf.
    Returns a single string with page contents separated by blank lines.
    """
    reader = PdfReader(str(pdf_path))
    parts: List[str] = []


    if type == "application":
        for page in reader.pages:
            text = page.extract_text() or ""
            cleaned = text.strip()
            if cleaned:
                parts.append(cleaned)
        return "\n\n".join(parts).strip()
    elif type == "presentation":
        for page in reader.pages:
            # Для презентаций используем layout mode для лучшего извлечения текста
            text: Optional[str] = page.extract_text(
                extraction_mode="layout",
                layout_mode_space_vertically=False,
            )

            cleaned = (text or "").strip()
            if cleaned:
                parts.append(cleaned)

        return "\n\n".join(parts).strip()
    else:
        raise ValueError(f"Invalid type: {type}")


