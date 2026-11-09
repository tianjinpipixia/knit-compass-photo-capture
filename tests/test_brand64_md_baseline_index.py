import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "md_baseline_index", ROOT / "scripts/publish_brand64_md_baseline_index.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RUN_SHA = "a" * 40
OLD_SHA = "b" * 40
DIGEST = "c" * 64


def binding(day="2026-11-09", run="42537080702"):
    return {
        "format": "KC_BRAND64_DAILY_PIPELINE_SNAPSHOT",
        "observation_date": day,
        "collection_run_id": run,
        "canonical_manifest_sha256": DIGEST,
        "canonical_status": "VALIDATED", "analysis_ready": True,
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True, "formal_product_registration": False,
    }


def record(day, sha=OLD_SHA, run="42526589272"):
    return {
        "observation_date": day, "bound_commit": sha,
        "collection_run_id": run, "canonical_manifest_sha256": DIGEST,
    }


class MdHistoryIndexTests(unittest.TestCase):
    def test_first_snapshot_creates_a_read_only_immutable_reference(self):
        result = mod.build_index(None, RUN_SHA, binding())
        self.assertEqual(result["format"], mod.FORMAT)
        self.assertEqual(result["branch"], "brand64/flash-feed")
        self.assertEqual(result["anchor_observation_date"], "2026-11-09")
        self.assertEqual(result["entries"], [record("2026-11-09", RUN_SHA, "42537080702")])
        self.assertFalse(result["index_is_run_success_proof"])
        self.assertEqual(result["publication_status"], "PUBLISH_HOLD")
        self.assertFalse(result["formal_product_registration"])

    def test_overwrite_same_day_but_retain_six_calendar_days(self):
        prior = {
            "format": mod.FORMAT, "branch": mod.BRANCH,
            "entries": [
                record("2026-11-09", OLD_SHA),
                record("2026-11-08", "d"*40),
                record("2026-11-07", "e"*40),
                record("2026-11-03", "f"*40),
                record("2026-11-02", "1"*40),
            ]
        }
        result = mod.build_index(prior, RUN_SHA, binding())
        self.assertEqual([x["observation_date"] for x in result["entries"]],
            ["2026-11-09", "2026-11-08", "2026-11-07", "2026-11-03"])
        self.assertEqual(result["entries"][0]["bound_commit"], RUN_SHA)

    def test_archive_expires_and_does_not_claim_missing_dates_complete(self):
        initial = mod.build_index(None, OLD_SHA, binding("2026-11-08", "42426589272"))
        result = mod.build_index(initial, RUN_SHA, binding("2026-11-16", "42537080702"))
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["entries"][0]["observation_date"], "2026-11-16")
        self.assertFalse(result["index_is_run_success_proof"])

    def test_invalid_provenance_and_publication_fail_closed(self):
        for mutate, name in [
            ({"canonical_manifest_sha256": "bad"}, "RECORD_INVALID"),
            ({"canonical_status": "FAILED"}, "NOT_VALIDATED"),
            ({"analysis_ready": False}, "NOT_VALIDATED"),
            ({"publication_status": "PUBLISHED"}, "PUBLICATION_BOUNDARY"),
            ({"formal_product_registration": True}, "PUBLICATION_BOUNDARY"),
            ({"observation_date": "2026-11-31"}, "DATE_INVALID"),
        ]:
            test = {**binding(), **mutate}
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "MD_BASELINE"):
                mod.build_index(None, RUN_SHA, test)
        with self.assertRaisesRegex(ValueError, "MD_BASELINE_SOURCE_COMMIT_INVALID"):
            mod.build_index(None, "not-a-git-commit", binding())

    def test_remote_push_failure_does_not_put_uncommitted_index_in_recovery_artifacts(self):
        # The actual workflow preserves the direct-scans folder after this step.
        # A failed push must not leave a falsely published local index there.
        for fail_push in (True, False):
            with self.subTest(fail_push=fail_push), tempfile.TemporaryDirectory() as folder:
                direct = Path(folder)
                index_file = direct / mod.INDEX
                original = b"previously saved contents"
                index_file.write_bytes(original)
                push_seen = []

                def fake_git(*args, **kwargs):
                    command = args[0]
                    if command == "rev-parse":
                        return subprocess.CompletedProcess(args, 0, (RUN_SHA + "\\n").encode(), b"")
                    if command == "show":
                        if str(args[1]).endswith("snapshot-binding.json"):
                            return subprocess.CompletedProcess(args, 0, json.dumps(binding()).encode(), b"")
                        return subprocess.CompletedProcess(args, 128, b"", b"fatal: path does not exist in source")
                    if command == "hash-object":
                        return subprocess.CompletedProcess(args, 0, (DIGEST[:40] + "\\n").encode(), b"")
                    if command == "write-tree":
                        return subprocess.CompletedProcess(args, 0, (OLD_SHA + "\\n").encode(), b"")
                    if command == "commit-tree":
                        return subprocess.CompletedProcess(args, 0, (RUN_SHA + "\\n").encode(), b"")
                    if command == "push":
                        self.assertEqual(index_file.read_bytes(), original)
                        push_seen.append(True)
                        if fail_push:
                            raise subprocess.CalledProcessError(1, ["git", *args])
                    return subprocess.CompletedProcess(args, 0, b"", b"")

                with patch.object(mod, "DIRECT", direct), patch.object(mod, "git", side_effect=fake_git):
                    if fail_push:
                        with self.assertRaises(subprocess.CalledProcessError):
                            mod.publish_index(binding(), expected_run_id="42537080702")
                        self.assertEqual(index_file.read_bytes(), original)
                    else:
                        result = mod.publish_index(binding(), expected_run_id="42537080702")
                        saved = json.loads(index_file.read_text())
                        self.assertEqual(saved["anchor_observation_date"], "2026-11-09")
                        self.assertEqual(result["bound_source_commit"], RUN_SHA)
                    self.assertTrue(push_seen)

    def test_invalid_prior_index_never_silently_replaced(self):
        broken = {"format": mod.FORMAT, "branch": mod.BRANCH, "entries": [record("wrong-date")]}
        with self.assertRaisesRegex(ValueError, "MD_BASELINE_DATE_INVALID"):
            mod.build_index(broken, RUN_SHA, binding())
        broken["entries"] = []
        broken["branch"] = "another-branch"
        with self.assertRaisesRegex(ValueError, "MD_BASELINE_INDEX_FORMAT_INVALID"):
            mod.build_index(broken, RUN_SHA, binding())


if __name__ == "__main__":
    unittest.main()
