"""Bridge one Docker-produced observation image to the host-local model boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "research" / "live_control"
if str(LIVE) not in sys.path:
    sys.path.insert(0, str(LIVE))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--token", default="docker2558")
    args = parser.parse_args()
    image = args.image.resolve(); out = args.out.resolve()
    if not image.is_file():
        raise SystemExit(f"missing observation image: {image}")
    import integrated_efficiency_model_v1 as model
    model.WINDOWS_PYTHON = Path(sys.executable)
    model.windows_path = lambda path: str(Path(path).resolve())
    prompt = ("Inspect the attached current Docker observation only. Return a "
              "schema-valid compiled-form-grounding-v1 object. The exact token "
              f"for the first action is {args.token}. Do not act, call tools, "
              "edit files, or claim task success.")
    result = model.call(out, prompt, image, "compiled", ROOT)
    envelope = {
        "schema": "docker-host-model-bridge-v1",
        "status": "GROUNDING_READY_NON_AUTHORITATIVE",
        "boundary": "docker-image-to-host-codex-exe",
        "image": str(image), "image_sha256": sha(image),
        "model_result": result, "authority_granted": False,
        "action_emitted": False, "task_success": "NOT_RUN",
        "next_gate": "fresh_focus_geometry_pixel_and_effect_validation"
    }
    (out / "bridge-result.json").write_text(json.dumps(envelope, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    print(json.dumps(envelope, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
