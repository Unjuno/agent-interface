from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api import dispatch, doctor
from .receipt import receipt_view
from .review import review
from .observe import observe


def _read_json(path: str):
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def _emit(payload) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(prog="agent-interface")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    read = sub.add_parser("observe")
    read.add_argument("--targets", required=True)
    read.add_argument("--target", required=True)
    read.add_argument("--frame", choices=("window_client", "screen_physical_px"), required=True)
    read.add_argument("--region", nargs=4, type=int, required=True, metavar=("X", "Y", "W", "H"))
    read.add_argument("--capture-directory")
    read.add_argument("--display")
    view = sub.add_parser("receipt")
    view.add_argument("--report", required=True)
    view.add_argument("--raw", action="store_true")
    image_review = sub.add_parser("review")
    image_review.add_argument("--report", required=True)
    image_review.add_argument("--run-directory", required=True)
    run = sub.add_parser("dispatch")
    run.add_argument("--program", required=True)
    run.add_argument("--targets", required=True)
    run.add_argument("--current-observation-seq", type=int, required=True)
    run.add_argument("--current-binding-revision", type=int, required=True)
    run.add_argument("--display")
    run.add_argument("--capture-directory")
    args = parser.parse_args()

    if args.command == "doctor":
        _emit(doctor())
        return 0
    if args.command == "review":
        try:
            row = review(args.report, args.run_directory)
        except (OSError, ValueError, TypeError) as error:
            _emit({"schema": "agent-interface/review-v1", "status": "invalid_receipt", "error": str(error)})
            return 2
        _emit(row)
        return 2 if row["image_status"] == "needs_review" else 0
    if args.command == "receipt":
        try:
            _emit(receipt_view(args.report, raw=args.raw))
        except (OSError, ValueError, TypeError) as error:
            _emit({"schema": "agent-interface/receipt-view-v1", "status": "invalid_receipt", "error": str(error)})
            return 2
        return 0
    if args.command == "observe":
        try:
            row = observe(_read_json(args.targets), target=args.target, frame=args.frame,
                          region=args.region, capture_directory=args.capture_directory,
                          display_name=args.display)
        except (OSError, ValueError, TypeError) as error:
            _emit({"status": "invalid_request", "error": str(error)})
            return 2
        _emit(row)
        return 0 if row["status"] == "returned" else 2
    try:
        program = _read_json(args.program)
        targets = _read_json(args.targets)
    except Exception as error:
        _emit({"schema": "agent-interface/runtime-dispatch-result-v1", "status": "invalid_request", "error": f"INVALID_JSON:{error}"})
        return 2
    row = dispatch(
        program,
        targets,
        current_observation_seq=args.current_observation_seq,
        current_binding_revision=args.current_binding_revision,
        display_name=args.display,
        capture_directory=args.capture_directory,
    )
    _emit(row)
    if row["status"] != "returned":
        return 2
    return 0 if row["result"].get("status") == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
