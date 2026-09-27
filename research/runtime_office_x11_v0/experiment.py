#!/usr/bin/env python3
"""Execute one bounded Calc edit through portable admission + OfficeX11Backend.

This process never imports openpyxl and never reads the workbook contents.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORTABLE = Path(os.environ['AGENT_INTERFACE_PORTABLE_ORACLE'])
X11 = Path(os.environ['AGENT_INTERFACE_X11_BACKEND'])
sys.path[:0] = [str(PORTABLE), str(X11), str(HERE)]
from contract import OFFICE_FLOOR, admit_program, capability_manifest  # noqa: E402
from office_backend import OfficeX11Backend  # noqa: E402


def program(pid: str, seq: int, revision: int, expires: int, ops: list[dict]) -> dict:
    if ops[-1].get('op') != 'release_all':
        ops = list(ops) + [{'op': 'release_all'}]
    return {
        'schema': 'agent-interface/program-v0', 'program_id': pid,
        'source': {'observation_seq': seq, 'binding_revision': revision},
        'authority': {'lease_id': 'calc-office-v0', 'expires_at_ns': expires},
        'ops': ops, 'terminal': {'release_all_required': True},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--display', required=True)
    ap.add_argument('--window-id', required=True, type=int)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    backend = OfficeX11Backend(args.display, {'calc': args.window_id})
    manifest = capability_manifest(
        'office-x11-private-v0', 'linux', 'x11', OFFICE_FLOOR,
        frames=('screen_physical_px', 'window_client'),
    )
    now = time.monotonic_ns(); future = now + 30_000_000_000
    stale = program('calc-stale', 6, 3, future, [
        {'op': 'focus', 'target': 'calc'},
        {'op': 'key_chord', 'keys': ['A']},
        {'op': 'release_all'},
    ])
    before = backend.emissions
    stale_admission = admit_program(
        stale, manifest, now_ns=time.monotonic_ns(),
        current_observation_seq=7, current_binding_revision=3,
    )
    stale_after = backend.emissions

    task = program('calc-edit-save', 7, 3, future, [
        {'op': 'focus', 'target': 'calc'},
        # Acquire the editable sheet surface before text entry. This coordinate
        # is fixture-bound, not a general Calc target-discovery claim.
        {'op': 'pointer_move', 'frame': 'window_client', 'x': 80, 'y': 180},
        {'op': 'pointer_button', 'button': 'left', 'down': True},
        {'op': 'pointer_button', 'button': 'left', 'down': False},
        {'op': 'key_chord', 'keys': ['CTRL', 'Home']},
        {'op': 'text', 'text': 'office'},
        {'op': 'key_chord', 'keys': ['ENTER']},
        {'op': 'text', 'text': 'preview'},
        {'op': 'key_chord', 'keys': ['ENTER']},
        {'op': 'key_chord', 'keys': ['CTRL', 'S']},
        # Existing XLSX invokes LibreOffice's format-confirmation dialog.
        {'op': 'wait_update', 'timeout_ms': 400},
        {'op': 'key_chord', 'keys': ['ENTER']},
        {'op': 'wait_update', 'timeout_ms': 1200},
        {'op': 'release_all'},
    ])
    admission = admit_program(
        task, manifest, now_ns=time.monotonic_ns(),
        current_observation_seq=7, current_binding_revision=3,
    )
    execution = backend.execute(task) if admission.accepted else None
    report = {
        'schema': 'agent-interface/office-x11-calc-execution-v0',
        'stale': {
            'accepted': stale_admission.accepted,
            'error': stale_admission.error,
            'emissions_before': before,
            'emissions_after': stale_after,
        },
        'task_admission': {'accepted': admission.accepted, 'error': admission.error},
        'task_execution': execution,
        'backend_emissions': backend.emissions,
        'release_verified': bool(execution and execution['releases'] and
                                 execution['releases'][-1]['verified'] and
                                 execution['releases'][-1]['keys_down'] == [] and
                                 execution['releases'][-1]['buttons_down'] == []),
        'scope': 'real LibreOffice Calc X11 execution; workbook semantics are scored only by a separate post-execution process',
    }
    report['passed_transport'] = all([
        not stale_admission.accepted,
        stale_admission.error == 'STALE_OBSERVATION',
        before == stale_after,
        admission.accepted,
        report['release_verified'],
    ])
    (args.out / 'execution.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    backend.close()
    print(json.dumps({'passed_transport': report['passed_transport'],
                      'backend_emissions': report['backend_emissions'],
                      'release_verified': report['release_verified']}, indent=2))
    return 0 if report['passed_transport'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
