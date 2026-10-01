"""Behavioral tests for the isolated #4947 runtime import bootstrap."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent


class RuntimeImportBootstrapTests(unittest.TestCase):
    def test_dynamo_external_utils_is_ready_before_mitra_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "torch" / "_dynamo").mkdir(parents=True)
            (root / "autogluon" / "tabular" / "models" / "mitra").mkdir(
                parents=True
            )
            for package in (
                "autogluon",
                "autogluon/tabular",
                "autogluon/tabular/models",
                "autogluon/tabular/models/mitra",
            ):
                (root / package / "__init__.py").write_text("", encoding="utf-8")
            (root / "torch" / "__init__.py").write_text("", encoding="utf-8")
            (root / "torch" / "_dynamo" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
            (root / "torch" / "_dynamo" / "external_utils.py").write_text(
                "READY = True\n", encoding="utf-8"
            )
            (root / "autogluon" / "tabular" / "models" / "mitra" / "sklearn_interface.py").write_text(
                "import torch._dynamo as dynamo\n"
                "if not hasattr(dynamo, 'external_utils'):\n"
                "    raise AttributeError('partially initialized torch._dynamo.external_utils')\n"
                "class MitraClassifier: pass\n",
                encoding="utf-8",
            )

            code = (
                "import sys; sys.path.insert(0, sys.argv[1]); "
                "from runtime_imports import load_mitra_runtime; "
                "torch, mitra_interface, classifier = load_mitra_runtime(); "
                "assert torch._dynamo.external_utils.READY is True; "
                "assert classifier is mitra_interface.MitraClassifier"
            )
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            result = subprocess.run(
                [sys.executable, "-c", code, str(root)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(
            result.returncode,
            0,
            f"bootstrap must import Dynamo external_utils before Mitra; "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}",
        )

    def test_candidate_runner_bootstraps_before_importing_mitra(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "torch" / "_dynamo").mkdir(parents=True)
            (root / "autogluon" / "tabular" / "models" / "mitra").mkdir(
                parents=True
            )
            for package in (
                "autogluon",
                "autogluon/tabular",
                "autogluon/tabular/models",
                "autogluon/tabular/models/mitra",
            ):
                (root / package / "__init__.py").write_text("", encoding="utf-8")
            (root / "torch" / "__init__.py").write_text("", encoding="utf-8")
            (root / "torch" / "_dynamo" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
            (root / "torch" / "_dynamo" / "external_utils.py").write_text(
                "READY = True\n", encoding="utf-8"
            )
            (root / "autogluon" / "tabular" / "models" / "mitra" / "sklearn_interface.py").write_text(
                "import torch._dynamo as dynamo\n"
                "if not hasattr(dynamo, 'external_utils'):\n"
                "    raise AttributeError('partially initialized torch._dynamo.external_utils')\n"
                "class MitraClassifier: pass\n",
                encoding="utf-8",
            )
            (root / "numpy.py").write_text("class ndarray: pass\n", encoding="utf-8")
            (root / "pandas.py").write_text("", encoding="utf-8")
            (root / "resource.py").write_text("", encoding="utf-8")
            (root / "label_abi.py").write_text(
                "def encode_labels(*args): return args\n"
                "def restore_probability_columns(*args): return args\n",
                encoding="utf-8",
            )

            code = (
                "import runpy, sys; from pathlib import Path; "
                "sys.path.insert(0, str(Path(sys.argv[2]).parent)); "
                "sys.path.insert(0, sys.argv[1]); "
                "runpy.run_path(sys.argv[2], run_name='bootstrap_probe'); "
                "import torch, torch._dynamo; "
                "assert torch._dynamo.external_utils.READY is True"
            )
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            runner = ROOT / "runner.py"
            result = subprocess.run(
                [sys.executable, "-c", code, str(root), str(runner)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(
            result.returncode,
            0,
            f"candidate runner must load Dynamo before Mitra; "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}",
        )


if __name__ == "__main__":
    unittest.main()

