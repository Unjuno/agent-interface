import subprocess
import tempfile
import unittest
from pathlib import Path

import check_workspace_index as workspace_index


class WorkspaceIndexTests(unittest.TestCase):
    def test_directory_discovery_uses_git_tree_when_checkout_is_sparse(self):
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            research = repository / "research"
            research.mkdir()
            (research / "README.md").write_text("index\n", encoding="utf-8")
            for name in ("alpha", "beta"):
                child = research / name
                child.mkdir()
                (child / "tracked.txt").write_text(name, encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "add", "research"], cwd=repository, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], cwd=repository, check=True)
            for name in ("alpha", "beta"):
                for path in (research / name).rglob("*"):
                    path.unlink()
                (research / name).rmdir()
            workspace_index.ROOT = research
            self.assertEqual(workspace_index.top_level_dirs(), {"alpha", "beta"})


if __name__ == "__main__":
    unittest.main()
