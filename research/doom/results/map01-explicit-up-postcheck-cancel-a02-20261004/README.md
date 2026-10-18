# Explicit-up cancellation boundary A02

A01 stopped before owner construction because the frozen source closure omitted `lease.py`; that first STOP and its stderr remain in the adjacent A01 package. A02 repairs only that import closure by adding the exact `lease.py` blob from frozen merge tree `71b723028a2db51a7f14a6db653d7f3789fa988b`. The tested owner and transition-wrapper bytes are unchanged.

This is one deterministic fake-Xlib construction attempt at the pre-dequeue cancellation / explicit-up side-effect boundary. OrbStack preflight is unavailable on this host (daemon content-blob `operation not supported`), so A02 is a host Python construction check and makes no container portability claim.

## Reproduction

```sh
python3 candidate.py
python3 audit.py
```

Run the candidate once only. `audit.py` reads the saved `RESULT.json`; it never calls the owner or repeats the interleaving. H/T/D/C/U are in `PLAN.md`; source hashes and the exact command are in `FREEZE.json`.
