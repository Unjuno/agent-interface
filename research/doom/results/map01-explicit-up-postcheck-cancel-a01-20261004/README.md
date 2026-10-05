# Explicit-up cancellation boundary A01

This one-shot construction probe tests a gap between the owner thread's pre-dequeue cancellation sample and the later explicit `up` side effect. It uses the exact `InputOwner v12` and `InputTransitionOwner v4` sources from the frozen PR stack, with a fake Xlib boundary and a deterministic queue hook. It performs no game, GUI, model, or real X11 operation.

The OrbStack Docker preflight stopped before candidate execution because the daemon could not open a content blob (`operation not supported`). The candidate therefore ran once on the macOS host under Python 3.14.5. This does not qualify container portability or Windows/WSLc behavior.

## Reproduction

From this directory:

```sh
python3 candidate.py
python3 audit.py
```

The candidate command is one-shot. Do not rerun it. `audit.py` only reads `RESULT.json`, tests saved-result mutations in memory, and writes `AUDIT.json`.

See `PLAN.md` for H/T/D/C/U, `FREEZE.json` for source hashes and gates, `ENVIRONMENT.json` for the preflight STOP, and `source_snapshot/` for exact source bytes. The first result and any failure are retained.
