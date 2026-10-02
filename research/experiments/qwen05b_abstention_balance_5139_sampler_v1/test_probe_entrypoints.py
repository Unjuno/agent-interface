import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


PACKAGE = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE.parents[2]


class ProbeEntrypointTests(unittest.TestCase):
    def run_probe(self, relative_path, expected_status):
        env = {
            key: value for key, value in os.environ.items()
            if key.casefold() != "pythonpath"
        }
        probe = PACKAGE / relative_path
        result = subprocess.run(
            [sys.executable, str(probe)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], expected_status)
        self.assertEqual(
            report.get("sentinels", report.get("sentinel_support_seeds", report.get("runs"))),
            128,
        )

    def test_feature_marginal_probe_runs_from_repository_root(self):
        self.run_probe(
            Path("evidence")
            / "feature-marginals-128-20260928"
            / "feature_design_probe.py",
            "PASS_STRATIFIED_SUPPORT_MARGINAL_FEASIBILITY_ONLY",
        )

    def test_joint_cell_probe_runs_from_repository_root(self):
        self.run_probe(
            Path("evidence")
            / "joint-cell-marginals-128-20260928"
            / "joint_matched_feature_probe.py",
            "PASS_JOINT_AND_MARGINAL_MATCHED_SET_FEASIBILITY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
