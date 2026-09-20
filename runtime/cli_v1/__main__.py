from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api import dispatch, doctor
from .receipt import receipt_view
from .review import review, review_bytes, present_result
from .observe import observe
from .attempt import invoke


def _read_json(path: str):
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def _emit(payload) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def _present_result(row, *, with_review, capture_directory, exit_code, compact=False, report_refs=False, retention=None):
    presented = (present_result(row, capture_directory, compact=compact, report_refs=report_refs)
                 if with_review else dict(row))
    if retention is not None:
        presented['retention'] = retention
        if not retention['report_persisted']:
            exit_code = exit_code or 2
    _emit(presented)
    return exit_code or (2 if with_review and presented['image_status'] == 'needs_review' else 0)


def main() -> int:
    parser = argparse.ArgumentParser(prog="agent-interface")
    sub = parser.add_subparsers(dest="command", required=True)
    diagnostic = sub.add_parser("doctor")
    diagnostic.add_argument('--check-dependencies', action='store_true',
                            help='inspect optional module discovery and installed versions without importing backends')
    read = sub.add_parser("observe")
    read.add_argument("--targets", required=True)
    read.add_argument("--target", required=True)
    read.add_argument("--frame", choices=("window_client", "screen_physical_px"), required=True)
    read.add_argument("--region", nargs=4, type=int, required=True, metavar=("X", "Y", "W", "H"))
    read.add_argument("--capture-directory")
    read.add_argument("--run-directory", help="reserve a fresh directory for request, raw result and images")
    read.add_argument("--display")
    read.add_argument("--review", action="store_true", help="return result and captured image together")
    read.add_argument("--compact", action="store_true", help="use smaller reversible receipt references with --review")
    read.add_argument("--report-refs", action="store_true", help="allow v3 report references; requires --compact and a compatible decoder")
    view = sub.add_parser("receipt")
    view.add_argument("--report", required=True)
    view.add_argument("--raw", action="store_true")
    image_review = sub.add_parser("review")
    image_review.add_argument("--report", required=True)
    image_review.add_argument("--run-directory", required=True)
    image_review.add_argument("--compact", action="store_true", help="replace duplicate receipt events with reversible local references")
    image_review.add_argument("--report-refs", action="store_true", help="allow v3 report references; requires --compact and a compatible decoder")
    run = sub.add_parser("dispatch")
    run.add_argument("--program", required=True)
    run.add_argument("--targets", required=True)
    run.add_argument("--current-observation-seq", type=int, required=True)
    run.add_argument("--current-binding-revision", type=int, required=True)
    run.add_argument("--display")
    run.add_argument("--capture-directory")
    run.add_argument("--run-directory", help="reserve a fresh directory for request, raw result and images")
    run.add_argument("--review", action="store_true", help="return result and last captured image together")
    run.add_argument("--compact", action="store_true", help="use smaller reversible receipt references with --review")
    run.add_argument("--report-refs", action="store_true", help="allow v3 report references; requires --compact and a compatible decoder")
    args = parser.parse_args()
    if args.command in ('observe', 'dispatch') and args.run_directory:
        if args.capture_directory:
            parser.error('--run-directory owns images; do not combine with --capture-directory')
        args.capture_directory = str(Path(args.run_directory).absolute() / 'images')
    if getattr(args, 'report_refs', False) and not args.compact:
        parser.error('--report-refs requires --compact')
    if args.command in ('observe', 'dispatch') and args.compact and not args.review:
        parser.error("--compact requires --review")
    if getattr(args, "review", False) and not args.capture_directory:
        parser.error("--review requires --capture-directory")

    if args.command == "doctor":
        _emit(doctor(check_dependencies=args.check_dependencies))
        return 0
    if args.command == "review":
        try:
            row = (review_bytes(sys.stdin.buffer.read(), args.run_directory, compact=args.compact, report_refs=args.report_refs) if args.report == "-"
                   else review(args.report, args.run_directory, compact=args.compact, report_refs=args.report_refs))
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
            row, retention = invoke(observe, dict(targets=_read_json(args.targets), target=args.target,
                          frame=args.frame, region=args.region, capture_directory=args.capture_directory,
                          display_name=args.display), args.run_directory, operation='observe')
        except (OSError, ValueError, TypeError) as error:
            _emit({"status": "invalid_request", "error": str(error)})
            return 2
        return _present_result(row, with_review=args.review, capture_directory=args.capture_directory,
                               exit_code=0 if row["status"] == "returned" else 2, compact=args.compact, report_refs=args.report_refs, retention=retention)
    try:
        program = _read_json(args.program)
        targets = _read_json(args.targets)
    except Exception as error:
        _emit({"schema": "agent-interface/runtime-dispatch-result-v1", "status": "invalid_request", "error": f"INVALID_JSON:{error}"})
        return 2
    row, retention = invoke(dispatch, dict(
        program=program, targets=targets,
        current_observation_seq=args.current_observation_seq,
        current_binding_revision=args.current_binding_revision,
        display_name=args.display, capture_directory=args.capture_directory),
        args.run_directory, operation='dispatch')
    code = 2 if row["status"] != "returned" else (0 if row["result"].get("status") == "completed" else 3)
    return _present_result(row, with_review=args.review, capture_directory=args.capture_directory, exit_code=code, compact=args.compact, report_refs=args.report_refs, retention=retention)


if __name__ == "__main__":
    raise SystemExit(main())
