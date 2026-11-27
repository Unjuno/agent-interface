from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_offline_package as package


class OfflinePackageTests(unittest.IsolatedAsyncioTestCase):
    def integration_path(self, root):
        path = Path(root) / "research/integration"
        path.mkdir(parents=True)
        return path

    async def test_reproducible_package_uses_pinned_entrypoint_and_keeps_zero_ledger(self):
        with tempfile.TemporaryDirectory() as root:
            integration = self.integration_path(root)
            first, second = integration / "first", integration / "second"
            first_manifest = await package.build(first)
            second_manifest = await package.build(second)
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual((first / package.MANIFEST).read_bytes(), (second / package.MANIFEST).read_bytes())
            self.assertEqual(package.verify_package(first), first_manifest)
            self.assertEqual((first / "task_oracle_server.py").read_bytes(),
                             package.pinned_input(package.R44, "task_oracle_server.py").read_bytes())
            self.assertEqual((first / "frozen_parent/conditions.json").read_bytes(),
                             (package.R44 / "conditions.json").read_bytes())
            self.assertEqual(list((first / "raw").iterdir()), [first / "raw/cohort-progress.json"])
            ledger = json.loads((first / "raw/cohort-progress.json").read_bytes())
            self.assertEqual((ledger["completed_trials"], ledger["trials"]), (0, []))

            template = json.loads((first / "conditions.template.json").read_bytes())
            prospective = json.loads((first / "conditions.json").read_bytes())
            self.assertEqual(prospective["trial"], prospective["trials"][0])
            self.assertFalse(template["execution_authorized"])
            self.assertFalse(prospective["execution_authorized"])
            self.assertTrue(all(t[key] is None for t in template["trials"] for key in package.ID_FIELDS))
            ids = [t[key] for t in prospective["trials"] for key in package.ID_FIELDS]
            self.assertEqual(len(set(ids)), 25)
            self.assertTrue(all(len(value) == 32 for value in ids))

            preflight = json.loads((first / "preflight.json").read_bytes())
            self.assertEqual([mode["mode"] for mode in preflight["modes"]], ["normal", "optimized"])
            self.assertTrue(preflight["published_root_resolvers_verified"])
            self.assertEqual({preflight[key] for key in (
                "fixture_launches", "tool_calls", "host_custody_accesses", "native_runtime_startups",
            )}, {0})
            for mode in preflight["modes"]:
                self.assertTrue(mode["direct_execution_refused"])
                self.assertTrue(mode["programmatic_execution_refused"])
                for path in ("task-mcp", "followup-recovery-mcp"):
                    proof = mode["paths"][path]
                    self.assertEqual(proof["entrypoint_arguments"][:3], [
                        "task_oracle_server.py", "raw/trial-01/targets.json", f"raw/trial-01/{path}",
                    ])
                    self.assertEqual(proof["registered_fake_tools"], list(package.REQUIRED_TOOLS))
                    self.assertFalse(proof["registration"]["task_oracle_invoked"])

    async def test_rejects_changed_pin_without_publishing_package(self):
        with tempfile.TemporaryDirectory() as root:
            frozen = Path(root) / "changed-parent"
            frozen.mkdir()
            (frozen / "conditions.json").write_bytes(b"{}")
            out = self.integration_path(root) / "unpublished"
            with patch.object(package, "R44", frozen):
                with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch for conditions.json"):
                    await package.build(out)
            self.assertFalse(out.exists())

    async def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            out = self.integration_path(root) / "package"
            out.mkdir()
            marker = out / "retained"
            marker.write_bytes(b"prior output")
            with self.assertRaises(FileExistsError):
                await package.build(out)
            self.assertEqual(list(out.iterdir()), [marker])
            self.assertEqual(marker.read_bytes(), b"prior output")

    async def test_rejects_nested_output_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            base = self.integration_path(root) / "outer"
            base.mkdir()
            target = base / "nested"
            with self.assertRaisesRegex(ValueError, "research/integration"):
                await package.build(target)
            self.assertFalse(target.exists())

    def test_checkout_line_endings_do_not_change_package_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "index"
            repository.mkdir()

            def git(*args, autocrlf=False):
                result = subprocess.run(
                    ["git", "-c", f"core.autocrlf={str(autocrlf).lower()}", *args],
                    cwd=repository, capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            git("init", "-q")
            for name in (".gitattributes", "input_pins.json", "offline_taskserver.py", "build_offline_package.py"):
                shutil.copyfile(package.HERE / name, repository / name)
            shutil.copytree(package.HERE / "inputs", repository / "inputs")
            (repository / "line-ending-probe.txt").write_bytes(b"normal checkout conversion\n")
            git("add", "--", ".")

            outputs = []
            for autocrlf in (False, True):
                with self.subTest(autocrlf=autocrlf):
                    source = root / f"checkout-{autocrlf}"
                    git("checkout-index", "--all", f"--prefix={source.as_posix()}/", autocrlf=autocrlf)
                    expected_ending = b"\r\n" if autocrlf else b"\n"
                    self.assertEqual((source / "line-ending-probe.txt").read_bytes(),
                                     b"normal checkout conversion" + expected_ending)
                    output = self.integration_path(root / f"build-{autocrlf}") / "r02"
                    args = ["-B", "-O"] if sys.flags.optimize else ["-B"]
                    result = subprocess.run(
                        [sys.executable, *args, "build_offline_package.py", "--output", str(output)],
                        cwd=source, capture_output=True, text=True, timeout=35,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    package.verify_package(output)
                    outputs.append((output / package.MANIFEST).read_bytes())

            self.assertEqual(len(outputs), 2)
            self.assertEqual(outputs[0], outputs[1])

    def test_manifest_rejects_unlisted_and_tampered_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            payload = out / "payload.txt"
            payload.write_bytes(b"initial data")
            (out / package.MANIFEST).write_text(f"{package.sha256(payload.read_bytes())}  payload.txt\n")
            self.assertEqual(len(package.verify_package(out)), 1)
            extra = out / "unlisted"
            extra.touch()
            with self.assertRaisesRegex(RuntimeError, "manifest does not match"):
                package.verify_package(out)
            extra.unlink()
            payload.write_bytes(b"modified data")
            with self.assertRaisesRegex(RuntimeError, "manifest does not match"):
                package.verify_package(out)


if __name__ == "__main__":
    unittest.main()
