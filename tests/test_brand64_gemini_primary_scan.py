import contextlib
import copy
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scan", ROOT / "scripts/run_brand64_gemini_primary_scan.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


class GeminiPrimaryScanTests(unittest.TestCase):
    def response(self, batch):
        return {
            "brands": [{"brand_id": b["brand_id"], "brand_name": b["brand_name"], "scan_status": "OK",
                        "official_listing_url": "https://official.example/knit", "notes": "", "surface_items": []} for b in batch],
            "_metadata": {"url_context_metadata": {"urlMetadata": [{"retrievedUrl": "https://official.example/knit",
                "urlRetrievalStatus": "URL_RETRIEVAL_STATUS_SUCCESS"}]}},
        }

    def test_gemini25_uses_tools_without_unsupported_structured_output(self):
        raw = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '```json\n{"brands": []}\n```'}]},
                              "groundingMetadata": {"groundingChunks": []}}]}
        with patch.object(scan.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(raw).encode())) as urlopen:
            result = scan.call_gemini("test-key", "gemini-2.5-flash", "test")
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertTrue(payload["tools"])
        self.assertNotIn("responseSchema", payload["generationConfig"])
        self.assertNotIn("responseMimeType", payload["generationConfig"])
        self.assertIn("grounding_metadata", result["_metadata"])

    def test_unfinished_json_response_is_rejected(self):
        raw = {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": '{"brands": []}'}]}}]}
        with patch.object(scan.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(raw).encode())):
            with self.assertRaisesRegex(RuntimeError, "not completed"):
                scan.call_gemini("test-key", "gemini-2.5-flash", "test")

    def test_unknown_duplicate_and_unexpected_brands_cannot_report_success(self):
        batch = [{"brand_id": "BR-TEST", "brand_name": "Test"}]
        for change in ["status", "duplicate", "unexpected"]:
            response = self.response(batch)
            if change == "status": response["brands"][0]["scan_status"] = "probably OK"
            if change == "duplicate": response["brands"] *= 2
            if change == "unexpected": response["brands"][0]["brand_id"] = "WRONG"
            with self.assertRaises(ValueError): scan.validated_rows(response, batch)

    def test_retrieval_evidence_is_required_and_failure_never_means_no_change(self):
        batch = [{"brand_id": "BR-TEST", "brand_name": "Test"}]
        response = self.response(batch)
        response["_metadata"] = {}
        row = scan.validated_rows(response, batch)[0]
        self.assertEqual(row["scan_status"], "SOURCE_EVIDENCE_MISSING")
        self.assertEqual(scan.compare(row, {"scan_status": "OK", "surface_items": []}), [])

    def test_incomplete_retry_preserves_successful_comparison_and_attempt_history(self):
        config = ROOT / "config/brand64-active-brands.json"
        brands = scan.active_brands(json.loads(config.read_text()))
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            argv = ["scan", "--config", str(config), "--output-root", str(root)]
            with patch.object(scan.sys, "argv", argv), patch.dict(scan.os.environ, {"GEMINI_API_KEY": "test-private-key"}), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(scan, "call_gemini", side_effect=[self.response(batch) for batch in scan.chunks(brands, 8)]):
                    self.assertEqual(scan.main(), 0)
                before = scan.pointer_state(root)
                saved = pathlib.Path(before["latest_comparable_artifact_path"])
                original = saved.read_bytes()
                with patch.object(scan, "call_gemini", side_effect=RuntimeError("failed test-private-key")):
                    self.assertEqual(scan.main(), 1)
            after = scan.pointer_state(root)
            self.assertEqual(after["gemini_execution_status"], "GEMINI_SCAN_INCOMPLETE")
            self.assertEqual(after["latest_comparable_artifact_path"], str(saved))
            self.assertEqual(saved.read_bytes(), original)
            self.assertNotEqual(after["artifact_path"], str(saved))
            self.assertEqual(scan.comparable_artifact(root, after)["gemini_execution_status"], "SUCCESS")
            self.assertNotIn("test-private-key", json.dumps(after))

    def test_missing_key_preserves_previous_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            pointer = {"latest_successful_scan_date": "2026-08-31", "latest_comparable_artifact_path": "previous.json"}
            a = scan.write_missing(root, scan.tokyo_today(), pointer, 64, "Missing key")
            b = scan.write_missing(root, scan.tokyo_today(), scan.pointer_state(root), 64, "Missing key")
            self.assertNotEqual(a, b)
            self.assertTrue(a.exists())
            self.assertEqual(scan.pointer_state(root)["latest_comparable_artifact_path"], "previous.json")

    def test_past_day_cannot_be_filled_with_today_observations(self):
        with patch.object(scan.sys, "argv", ["scan", "--date", "1999-01-01"]), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(scan, "call_gemini") as call:
                with self.assertRaises(SystemExit): scan.main()
                call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
