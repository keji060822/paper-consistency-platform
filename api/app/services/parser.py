from __future__ import annotations

import io
from pathlib import Path
import zipfile


TEXT_SUFFIXES = {
    ".txt",
    ".tex",
    ".md",
    ".csv",
    ".json",
    ".bib",
    ".cls",
    ".sty",
    ".xml",
    ".yaml",
    ".yml",
}


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "gb18030", "latin1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data:
        return True

    sample = data[:4096]
    non_text_bytes = sum(1 for byte in sample if byte < 9 or (13 < byte < 32))
    return non_text_bytes / max(len(sample), 1) > 0.3


def _extract_text_from_zip(data: bytes) -> str:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError("Uploaded ZIP file is invalid.") from exc

    chunks: list[str] = []
    for item in sorted(archive.infolist(), key=lambda entry: entry.filename.lower()):
        if item.is_dir():
            continue
        suffix = Path(item.filename).suffix.lower()
        if suffix not in TEXT_SUFFIXES:
            continue

        content = archive.read(item)
        if not content or _looks_binary(content):
            continue

        text = _decode_text(content).strip()
        if text:
            chunks.append(text)

    if not chunks:
        raise ValueError(
            "No readable text found in uploaded ZIP. Include .tex/.txt/.md files."
        )
    return "\n\n".join(chunks)


def parse_file_bytes(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix in TEXT_SUFFIXES:
        return _decode_text(data)

    if suffix == ".zip":
        return _extract_text_from_zip(data)

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

        try:
            reader = PdfReader(io.BytesIO(data))
        except Exception as exc:
            raise ValueError(
                "Failed to read PDF file. It may be encrypted, image-only, or malformed."
            ) from exc

        pages: list[str] = []
        for page in reader.pages:
            try:
                extracted = page.extract_text() or ""
            except Exception:
                continue
            if extracted.strip():
                pages.append(extracted.strip())
        return "\n".join(pages)

    if _looks_binary(data):
        raise ValueError(
            "Unsupported binary file content. Please upload PDF, DOCX, LaTeX ZIP, or text files."
        )

    return _decode_text(data)
