from __future__ import annotations

import io
from pathlib import Path


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "gb18030", "latin1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def parse_file_bytes(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix in {".txt", ".tex", ".md", ".csv", ".json"}:
        return _decode_text(data)

    if suffix == ".docx":
        try:
            from docx import Document  # type: ignore
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise ValueError("DOCX support requires python-docx. Please install dependencies.") from exc

        doc = Document(io.BytesIO(data))
        lines = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()]
        return "\n".join(lines)

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise ValueError("PDF support requires pypdf. Please install dependencies.") from exc

        reader = PdfReader(io.BytesIO(data))
        pages: list[str] = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            if extracted.strip():
                pages.append(extracted.strip())
        return "\n".join(pages)

    return _decode_text(data)

