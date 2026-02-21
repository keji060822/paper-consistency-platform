import pathlib
import sys
import types
import unittest
import zipfile
from io import BytesIO
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.services.parser import parse_file_bytes


class ParserTests(unittest.TestCase):
    def test_pdf_tolerates_single_page_extract_error(self) -> None:
        class BrokenPage:
            def extract_text(self) -> str:
                raise RuntimeError("page parse error")

        class GoodPage:
            def extract_text(self) -> str:
                return "Useful content."

        class FakePdfReader:
            def __init__(self, _stream) -> None:
                self.pages = [BrokenPage(), GoodPage()]

        fake_module = types.SimpleNamespace(PdfReader=FakePdfReader)
        with patch.dict(sys.modules, {"pypdf": fake_module}):
            text = parse_file_bytes("sample.pdf", b"%PDF-1.7")

        self.assertIn("Useful content.", text)

    def test_pdf_reader_init_error_returns_value_error(self) -> None:
        class FakePdfReader:
            def __init__(self, _stream) -> None:
                raise RuntimeError("invalid pdf")

        fake_module = types.SimpleNamespace(PdfReader=FakePdfReader)
        with patch.dict(sys.modules, {"pypdf": fake_module}):
            with self.assertRaisesRegex(ValueError, "Failed to read PDF"):
                parse_file_bytes("broken.pdf", b"%PDF-1.7")

    def test_zip_latex_extracts_text_content(self) -> None:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("paper/main.tex", "Threshold window is defined in Section 2.")
            archive.writestr("paper/refs.bib", "@article{a, title={test}}")
            archive.writestr("paper/image.png", b"\x89PNG\r\n\x1a\n")

        text = parse_file_bytes("paper.zip", buffer.getvalue())
        self.assertIn("Threshold window is defined in Section 2.", text)
        self.assertNotIn("PNG", text)

    def test_zip_without_readable_text_raises_value_error(self) -> None:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("images/figure.png", b"\x89PNG\r\n\x1a\n")
            archive.writestr("images/raw.bin", b"\x00\x01\x02\x03")

        with self.assertRaisesRegex(ValueError, "No readable text found in uploaded ZIP"):
            parse_file_bytes("figures.zip", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
