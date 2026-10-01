"""Create the pre-run immutable source/image manifest for the live probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    here = Path(__file__).resolve().parent
    rel_here = here.relative_to(repo).as_posix()
    producer_sources = [
        "live_control/interactive_v17.py", "live_control/receipt_journal.py",
        "live_control/delivery_ledger_v2.py", "live_control/presentation_v2.py",
        "live_control/session_v16.py", "live_control/patch_servo.py",
        "live_control/visual_anchor.py", "live_control/session_v15.py",
        "live_control/session_v13.py", "live_control/session_v12.py",
        "live_control/session_v11.py", "live_control/input_owner_v9.py",
        "live_control/pointer_reply_v2.py", "live_control/session_v9.py",
        "live_control/input_owner_v5.py", "live_control/presentation.py",
        "live_control/session_v8.py", "live_control/quiet_window.py",
        "live_control/session_v7.py", "live_control/session_v6.py",
        "live_control/input_owner_v2.py", "live_control/session_v5.py",
        "live_control/input_owner.py", "live_control/executor_v3.py",
        "live_control/session_v4.py", "live_control/lease.py",
        "observation_tiles/tile_transport.py", "observation_tiles/image_artifact.py",
        "observation_gating/gui_suite.py", "observation_gating/exact_gate.py",
        "real_apps_v1/real_app_suite_v1.py",
    ]
    paths = {
        f"research/{value}" for value in producer_sources
    } | {
        "research/integration/event_inbox_reader_v1/__main__.py",
        "research/integration/event_inbox_reader_v1/reader.py",
        f"{rel_here}/README.md", f"{rel_here}/Dockerfile",
        f"{rel_here}/CONSTRUCTION.md",
        f"{rel_here}/requirements-live.txt", f"{rel_here}/freeze.py",
        f"{rel_here}/runner.py", f"{rel_here}/audit.py",
    }
    inputs = {name: digest(repo / name) for name in sorted(paths)}
    manifest = {
        "schema": "issue-3876-live-reader-freeze-v1",
        "base_commit": "cc9c500a339406c7de71df04c1d4b23f12fdbb09",
        "base_image_id": "sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3",
        "image_id": args.image_id,
        "platform": "linux/amd64",
        "allocation": "issue-3876-live-reader-20260921-01",
        "stream_id": "interactive-v17-calc-387601-epoch-01",
        "producer_command": [
            "python3", "research/live_control/interactive_v17.py", "--app", "calc",
            "--seed", "387601", "--presentation", "full",
        ],
        "reader_sequence": ["live-prefix-before-finish", "terminal-suffix", "final-empty"],
        "input_commands": ["clock", "finish"],
        "inputs": inputs,
        "source_count": len(inputs),
        "python_packages": [
            "Pillow==11.3.0", "python-xlib==0.33", "openpyxl==3.1.5",
            "numpy==2.2.6", "six==1.17.0", "et-xmlfile==2.0.0",
        ],
    }
    out = args.out.resolve()
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"freeze_path": str(out), "source_count": len(inputs),
                      "image_id": args.image_id}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
