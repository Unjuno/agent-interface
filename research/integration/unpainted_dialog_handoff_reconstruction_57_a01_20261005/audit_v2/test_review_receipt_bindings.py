import hashlib
import io
import json
import subprocess
import sys
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[4]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewReceiptBindingTests(unittest.TestCase):
    def test_audit_rejects_review_receipt_detached_from_returned_reply(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "research/integration" / PACKAGE.name
            archive = subprocess.run(
                [
                    "git", "-C", str(REPOSITORY), "archive", "--format=tar", "HEAD",
                    f"research/integration/{PACKAGE.name}",
                    "research/live_control/results/recovery-assistant-01",
                    "runtime/host_v1", "docs/INTEGRATION_PLAN.md",
                ],
                capture_output=True,
                check=True,
            )
            with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
                bundle.extractall(root)
            shutil.copytree(PACKAGE / "audit_v2", package / "audit_v2", dirs_exist_ok=True)

            source_manifest = package / "SHA256SUMS"
            source_rows = source_manifest.read_text(encoding="ascii").splitlines()
            source_manifest.write_text(
                "\n".join(
                    f"{sha256(source_manifest.parent / rel)}  {rel}"
                    for _, rel in (line.split("  ", 1) for line in source_rows)
                ) + "\n",
                encoding="ascii",
            )

            review_path = package / "replay_raw/a01_20261005/review-1.json"
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["reply_sha256"] = "0" * 64
            review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")

            for run_id in ("a01_20261005", "a02_20261005"):
                events_path = package / "replay_raw" / run_id / "host-events.jsonl"
                events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
                for event in events:
                    if event.get("kind") == "presentation_callbacks_completed":
                        delivered_reply_sha = sha256(
                            package / "replay_raw" / run_id / f"reply-{event['attempt']}.json"
                        )
                        event["reply_sha256"] = delivered_reply_sha
                events_path.write_text(
                    "\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8", newline="\n"
                )

            manifest = package / "REPLAY_SHA256SUMS"
            rows = manifest.read_text(encoding="ascii").splitlines()
            target = "a01_20261005/review-1.json"
            rows = [
                f"{sha256(package / 'replay_raw' / target)}  {target}"
                if line.split("  ", 1)[1] == target else line
                for line in rows
            ]
            rows = [f"{sha256(package / 'replay_raw' / rel)}  {rel}" for line in rows
                    for _, rel in [line.split("  ", 1)]]
            manifest.write_text("\n".join(rows) + "\n", encoding="ascii")

            v1 = subprocess.run(
                [sys.executable, str(package / "audit_replay.py")],
                cwd=root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(v1.returncode, 0, v1.stdout + v1.stderr)

            result = subprocess.run(
                [sys.executable, str(package / "audit_v2/audit_replay_v2.py")],
                cwd=root, capture_output=True, text=True, check=False,
            )

            self.assertNotEqual(
                result.returncode,
                0,
                "the v2 replay auditor accepted a review receipt whose reply digest does not match the delivered reply",
            )


if __name__ == "__main__":
    unittest.main()
