import hashlib
import json
import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[4]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay_sha256(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class ReviewReceiptBindingTests(unittest.TestCase):
    def _copy_package(self, root):
        package = root / "research/integration" / PACKAGE.name
        shutil.copytree(PACKAGE, package)
        for line in (PACKAGE / "SHA256SUMS").read_text(encoding="ascii").splitlines():
            _, rel = line.split("  ", 1)
            source = (PACKAGE / rel).resolve()
            destination = (package / rel).resolve()
            if source != destination:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        return package

    @staticmethod
    def _refresh_replay_manifest(package, changed_paths):
        manifest = package / "REPLAY_SHA256SUMS"
        rows = [line.split("  ", 1)[1] for line in manifest.read_text(encoding="ascii").splitlines()]
        for rel in changed_paths:
            if rel not in rows:
                raise AssertionError(f"changed replay file is not manifested: {rel}")
        manifest.write_text(
            "".join(f"{replay_sha256(package / 'replay_raw' / rel)}  {rel}\n" for rel in rows),
            encoding="ascii",
            newline="\n",
        )

    def _run_v2(self, package):
        return subprocess.run(
            [sys.executable, str(package / "audit_v2/audit_replay_v2.py")],
            cwd=package.parents[2], capture_output=True, text=True, check=False,
        )

    def test_audit_accepts_unchanged_retained_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            package = self._copy_package(Path(temp))
            result = self._run_v2(package)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_audit_rejects_review_receipt_detached_from_returned_reply(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._copy_package(root)

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
            review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8", newline="\n")

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
            manifest.write_text("\n".join(rows) + "\n", encoding="ascii", newline="\n")

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

    def test_audit_rejects_receipt_and_event_relabelled_to_wrong_relay_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._copy_package(root)
            run_id = "a01_20261005"
            attempt = 1

            review_path = package / "replay_raw" / run_id / f"review-{attempt}.json"
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["relay_id"] = 999
            review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8", newline="\n")

            events_path = package / "replay_raw" / run_id / "host-events.jsonl"
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            availability = [event for event in events if event.get("kind") == "reply_available" and event.get("attempt") == attempt]
            self.assertEqual(len(availability), 1)
            availability[0]["relay_id"] = 999
            events_path.write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8", newline="\n"
            )
            self._refresh_replay_manifest(package, [
                f"{run_id}/review-{attempt}.json", f"{run_id}/host-events.jsonl",
            ])

            result = self._run_v2(package)
            self.assertNotEqual(
                result.returncode,
                0,
                "the v2 replay auditor accepted matching but incorrect receipt and event relay IDs",
            )

    def test_audit_rejects_presentation_started_with_detached_reply_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._copy_package(root)
            run_id = "a01_20261005"
            attempt = 1

            events_path = package / "replay_raw" / run_id / "host-events.jsonl"
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            started = [event for event in events if event.get("kind") == "presentation_started" and event.get("attempt") == attempt]
            self.assertEqual(len(started), 1)
            started[0]["reply_sha256"] = "0" * 64
            events_path.write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8", newline="\n"
            )
            self._refresh_replay_manifest(package, [f"{run_id}/host-events.jsonl"])

            result = self._run_v2(package)
            self.assertNotEqual(
                result.returncode,
                0,
                "the v2 replay auditor accepted a presentation_started event detached from its reply",
            )


if __name__ == "__main__":
    unittest.main()
