"""Freeze current-main source and the pending-invalidation candidate before run."""
import hashlib
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOOM = HERE.parent
sys.path.insert(0, str(DOOM))
sys.path.insert(0, str(DOOM.parent / "live_control"))
import map01_overlap_controller_v39  # noqa: F401


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = {}
repo_root = REPO.resolve()
for module in tuple(sys.modules.values()):
    path_text = getattr(module, "__file__", None)
    if not path_text or not path_text.endswith(".py"):
        continue
    path = Path(path_text).resolve()
    try:
        relative = path.relative_to(repo_root).as_posix()
    except ValueError:
        continue
    manifest[relative] = sha256(path)

candidate = HERE / "test_pending_invalidation.py"
manifest[candidate.relative_to(REPO).as_posix()] = sha256(candidate)
freeze = {
    "schema": "v39-pending-model-invalidation-a01-freeze-v1",
    "repository": "Unjuno/agent-interface",
    "main_sha": "e724d6d795da2852c043cb53cfd92d5a9222a091",
    "run_kind": "local AST-extracted controller construction interleaving",
    "formal_allocation": False,
    "game_model_provider_gui_os_input": False,
    "source_manifest_sha256": dict(sorted(manifest.items())),
    "python": sys.version,
    "platform": platform.platform(),
    "planned_commands": [
        "python -m unittest research.doom.v39_pending_model_invalidation_a01_20261005.test_pending_invalidation -v",
        "python -O -m unittest research.doom.v39_pending_model_invalidation_a01_20261005.test_pending_invalidation -v",
    ],
}
(HERE / "FREEZE.json").write_text(
    json.dumps(freeze, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"freeze": str(HERE / "FREEZE.json"),
                  "manifest_files": len(manifest),
                  "main_sha": freeze["main_sha"]}, sort_keys=True))
