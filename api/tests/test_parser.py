import pathlib
import sys
import types
import unittest
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


if __name__ == "__main__":
    unittest.main()
