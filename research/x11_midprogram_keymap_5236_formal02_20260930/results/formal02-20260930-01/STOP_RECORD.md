# Formal allocation 01 — STOP

This is the immutable outcome of the one authorized invocation for allocation `issue5236-formal02-20260930-01`. Do not retry or alter this result. No successor row was run.

- Frozen source commit: `460705e49f8f7271362710cb7b6cbcd7d28bb3cc`.
- Command: `python -B -m research.x11_midprogram_keymap_5236_formal02_20260930.runner --output research/x11_midprogram_keymap_5236_formal02_20260930/results/formal02-20260930-01`.
- Wrapper exit: 1; timeout: false; child raw record: absent.
- Failure: child launched `runner.py` by absolute script path; Python placed the research bundle directory, but not repository root, on `sys.path`. Import failed before namespace setup or any Xvfb launch: `ModuleNotFoundError: No module named 'runtime'`.
- Host WSLg socket metadata was unchanged (mode 0777, inode 2, device 38). Process inspection found no Xvfb, setxkbmap actor, or fixture process remaining.
- `wrapper.json` retains the exact command, stderr traceback, exit, source manifest, and host socket before/after metadata. No `raw.json` exists because the child failed before entering `child_main`.

Classification: `STOP_PROVENANCE_OR_RUNNER` (frozen runner launch defect). This STOP is immutable. A corrected launcher requires a separately frozen successor allocation with a new output path; no retry is permitted here.
