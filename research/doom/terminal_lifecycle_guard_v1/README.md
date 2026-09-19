# Terminal lifecycle guard — research only

Read REPORT.md for the capability boundary. No production runtime file is changed.

Repository-only tests (Python standard library):

```sh
cd research/doom/terminal_lifecycle_guard_v1
python -m unittest test_gate test_acquisition -v
```

Full evidence replay requires the supplied evidence.tar.xz (see archive.json): verify
its SHA-256, extract to a fresh directory, then run:

```sh
python replay.py /path/to/extracted/evidence-root --pixels
EVIDENCE_ROOT=/path/to/extracted/evidence-root python -m unittest test_gate test_acquisition test_audit -v
```

Pillow is required for pixels. The extraction contains evidence/, runtime-source/,
discovery-source/ and manifest.json. This runtime-source is a READ-ONLY replay
closure, not a complete executable distribution. A new live run needs the complete
pinned runtime/wheel bundle from GitHub Actions artifact 10398313098, a separate
virtual environment, Xvfb/Openbox and a new plan/output ID. Never copy the snapshot
over an ordinary product runtime directory. `run.py` rejects source/fixture pin
mismatches and existing case output directories. The plans in this directory are
consumed; do not restart them as new evidence.

All clocks are local monotonic ns. Success classification is still intentionally
reported as mismatched for the timeout counterexample; it must not be silently
promoted to a successful game episode.
