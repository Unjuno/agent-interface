import unittest
import tempfile
from pathlib import Path

import launch_contract


class LaunchContractTests(unittest.TestCase):
    def test_launch_main_freeze_matches_expected_inventory(self):
        expected = __import__("json").loads(
            (Path(__file__).parent / "EXPECTED.json").read_text(encoding="utf-8"))
        self.assertEqual(launch_contract._FROZEN_MAIN, expected["frozen_main"])

    def require_builder(self):
        builder = getattr(launch_contract, "build_command", None)
        self.assertTrue(callable(builder), "Docker launch contract builder is missing")
        return builder

    def paths(self):
        workdir = Path(__file__).resolve().parent
        return workdir, workdir / "results" / "formal-01"

    def image(self):
        return launch_contract._IMAGE_REF

    def test_overrides_python_entrypoint_and_preflights_xlib_before_fixture(self):
        builder = self.require_builder()
        image = self.image()
        workdir, results_dir = self.paths()
        try:
            command = builder(
                workdir=workdir,
                results_dir=results_dir,
                image=image,
                platform="linux/amd64",
            )
        except ValueError as error:
            self.fail(f"valid digest-pinned image reference was rejected: {error}")
        except TypeError as error:
            self.fail(f"builder does not isolate read-only source and writable results: {error}")

        image_at = command.index(image)
        self.assertEqual(command[image_at - 2:image_at], ["--entrypoint", "/bin/sh"])
        script = command[image_at + 1:]
        self.assertEqual(script[0], "-ceu")
        self.assertIn('python3 -c "import Xlib; from Xlib import display"', script[1])
        self.assertLess(script[1].index("import Xlib"), script[1].index("xvfb-run"))
        self.assertIn("command -v timeout", script[1])
        self.assertIn("FORMAL_ALLOCATION=MAP01-OWNER-KEYUP-BRACKET-5156-20261001-06", script[1])
        self.assertIn("FORMAL_FROZEN_MAIN=9fc98feb617c26fe1baa7ecc4decd43b69df8601", script[1])
        self.assertIn("FORMAL_IMAGE_DIGEST=sha256:f41b02e63fc3964f9bb831167ae42bce6d6ffa50fbda122d22deaa39736637bb", script[1])
        self.assertIn("FORMAL_PLATFORM=linux/amd64", script[1])
        self.assertIn("FORMAL_V11_DIR=/src/dependencies", script[1])
        source_mount = f"type=bind,source={workdir.resolve().as_posix()},target=/src,readonly"
        results_mount = f"type=bind,source={results_dir.resolve().as_posix()},target=/results"
        self.assertIn(source_mount, command)
        self.assertIn(results_mount, command)
        self.assertIn("--read-only", command)
        self.assertIn("/tmp:rw,noexec,nosuid,size=32m", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertIn("exec timeout --signal=TERM --kill-after=2s 300s xvfb-run -a python3 /src/run_formal_x11.py /results/raw.jsonl", script[1])

    def test_never_pulls_and_disables_runtime_network(self):
        try:
            command = self.require_builder()(
                workdir=self.paths()[0],
                results_dir=self.paths()[1],
                image=self.image(),
                platform="linux/amd64",
            )
        except ValueError as error:
            self.fail(f"valid digest-pinned image reference was rejected: {error}")

        self.assertIn("--pull=never", command)
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertIn("--cpus=1", command)
        self.assertIn("--memory=512m", command)
        self.assertIn("--pids-limit=64", command)

    def test_auditor_runs_as_a_separate_raw_only_invocation(self):
        builder = getattr(launch_contract, "build_audit_command", None)
        self.assertTrue(callable(builder), "separate raw-only audit argv builder is missing")
        workdir, results_dir = self.paths()
        image = self.image()
        try:
            command = builder(workdir, results_dir, image, "linux/amd64")
        except TypeError as error:
            self.fail(f"audit builder does not accept isolated source/output mounts: {error}")

        image_at = command.index(image)
        script = command[image_at + 1:]
        self.assertIn("exec timeout --signal=TERM --kill-after=2s 120s python3 /src/audit_formal_x11.py /results/raw.jsonl /src/EXPECTED.json /results/audit.json",
                      script[1])
        self.assertNotIn("xvfb-run", script[1])
        self.assertIn("--network", command)
        self.assertEqual(command[command.index("--network") + 1], "none")

    def test_rejects_non_digest_or_wrong_platform_before_launch(self):
        builder = self.require_builder()
        workdir, results_dir = self.paths()

        with self.assertRaises(ValueError):
            builder(workdir, results_dir, "python:latest", "linux/amd64")
        with self.assertRaisesRegex(ValueError, "platform"):
            builder(workdir, results_dir, self.image(), "linux/arm64")
        with self.assertRaises(ValueError):
            builder(workdir, results_dir, "sha256:" + "e" * 64, "linux/amd64")
        with self.assertRaisesRegex(ValueError, "frozen locally cached"):
            builder(workdir, results_dir, self.image().split("@sha256:")[0] + "@sha256:" + "d" * 64,
                    "linux/amd64")
        with self.assertRaises(ValueError):
            builder(Path("C:/repo"), results_dir, self.image(), "linux/amd64")
        with self.assertRaisesRegex(ValueError, "results directory"):
            builder(workdir, workdir / "results" / "arbitrary", self.image(), "linux/amd64")

    def test_rejects_missing_source_or_results_mount_before_launch(self):
        builder = self.require_builder()
        workdir, results_dir = self.paths()
        image = self.image()
        with self.assertRaisesRegex(ValueError, "workdir must exist"):
            missing = Path("C:/tmp/research/live_control/owner_keyup_formal_x11_5156_20261001_06")
            builder(missing, missing / "results" / "formal-01", image, "linux/amd64")
        with tempfile.TemporaryDirectory() as temporary:
            isolated = Path(temporary) / "research" / "live_control" / workdir.name
            isolated.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "results directory must exist"):
                builder(isolated, isolated / "results" / "formal-01", image, "linux/amd64")


if __name__ == "__main__":
    unittest.main()
