# Mode-flap diagnostic T0 A01 — Issue #7505

Status: `STOP_INFRASTRUCTURE` before container creation. WSLc rejected the frozen `--cidfile /out/candidate.cid` argument because it resolves that CID-file path on the host, where `/out` does not exist. The command, first stdout and exit code are preserved under `formal_a01/`; no candidate program ran, no raw result exists, and no scientific inference is available. A corrected later execution must use a new allocation ID, distinct frozen inputs, and a revised invocation record. A01 will not be retried.

Read [PREREG.md](PREREG.md) for frozen H/T/D/C/U, comparator definitions, thresholds, outcome criteria, and execution limits. The fixture covers endogenous flicker, demand drift, noisy single-mode telemetry, policy oscillation without loss, abrupt failure, and stable service. `candidate.py` emits the complete event ledger; `audit.py` independently replays it and checks corruption controls.

This is a finite synthetic method result only. It does not establish a warning for a real verifier, computer-control runtime, service, or user task; it estimates no operational false-alarm rate and authorizes no damping or control response.
