import pathlib
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.main import app


class ApiConfigTests(unittest.TestCase):
    def test_root_route_renders_html_landing(self) -> None:
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("论文一致性检测 API", response.text)
        self.assertIn("打开 API 文档", response.text)

    @patch("app.main.GLMClient.review", return_value=[])
    def test_request_api_key_can_enable_glm(self, _mock_review) -> None:
        client = TestClient(app)
        text = "This is a simple sentence."

        response = client.post(
            "/api/analyze",
            files={"file": ("sample.txt", text.encode("utf-8"), "text/plain")},
            data={
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "model": "glm-4.5-flash",
                "api_key": "test-key-from-ui",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["engine"]["glm_enabled"])
        self.assertTrue(body["engine"]["glm_attempted"])

    def test_health_allows_null_origin_for_file_preview(self) -> None:
        client = TestClient(app)
        response = client.get("/health", headers={"Origin": "null"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "null")


if __name__ == "__main__":
    unittest.main()
