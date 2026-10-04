"""Live v1 caller with reversible stdout view and original on-disk report.

Input semantics are delegated unchanged. Presentation never retries a program.
The caller's original continuation_batch is retained in report.json.
"""
import argparse
import json
from pathlib import Path
from pointer_exchange_v1 import run
from pointer_report_view_v1 import pack, unpack
from unix_json_deadline import exchange


def main():
    ap = argparse.ArgumentParser()
    for name in ('socket', 'batch', 'run_directory', 'program_id', 'steps'):
        ap.add_argument(name)
    ap.add_argument('--lease-ms', type=int, default=30000)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    def persist(name, value):
        (args.out / (name + '.json')).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

    batch = json.loads(Path(args.batch).read_text())
    steps = json.loads(Path(args.steps).read_text())
    persist('source-batch', batch)
    persist('steps', steps)
    report = run(lambda request: exchange(args.socket, request, timeout=16), batch,
                 args.run_directory, args.program_id, steps, args.lease_ms, persist)
    persist('report', report)
    view = pack(report)
    if json.dumps(unpack(view), sort_keys=True) != json.dumps(report, sort_keys=True):
        raise ValueError('presentation round-trip failed; original report retained, do not resend input')
    persist('view', view)
    print(json.dumps(view, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
