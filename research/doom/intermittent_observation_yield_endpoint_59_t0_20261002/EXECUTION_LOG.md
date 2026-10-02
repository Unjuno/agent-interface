# Execution log

This log distinguishes the read-only predecessor diagnostic and TDD construction check from the one candidate and one auditor invocation. Source hashes were taken only after the candidate invocation; see `STOP.json`.

## Predecessor red evidence

Source: immutable #6297 candidate SHA-256 `094f55b27489b32ce6409b1a93e63c88eb27129ab7bd9e2d4350930f8622976c`; independent oracle SHA-256 `cd0cda51fc5a203cb13b42e4ad4a01edcb1f1b97fad5031c7a4d64431e8fb4ac`.

At interval `[100,200]`, the read-only probe observed candidate/oracle decisions of YIELD/YIELD at 199, CONTINUE/YIELD at 200, and CONTINUE/CONTINUE at 201. The regression assertion at 200 exited 1 with expected `YIELD_CAPTURE_ORDER_UNKNOWN`, actual `CONTINUE`. No predecessor `main()` or output-writing entrypoint was run; the predecessor package was not modified.

## Successor commands and outputs

- `python3 -m unittest discover -s yield_endpoint_successor -p test_endpoint.py` — exit 0; one unittest with five subcases; stdout: `.` then `Ran 1 test ... OK`.
- `python3 run_candidate.py` — exit 0; stdout: `{"continue": 1, "raw_sha256": "dcd2cc6a4c4345aaee40f1150866feb1bce1e134721b76e14bac8a67e1a596dd", "rows": 5, "status": "CANDIDATE_COMPLETE", "yield": 4}`.
- `python3 audit.py` — exit 0; stdout is retained verbatim in `results/formal-01/audit.json`; zero errors and four corruption controls rejected.
- `python3 -m json.tool` on fixture, STOP, raw and audit JSON — exit 0.
- `shasum -a 256 ...` source/output inventory — hashes retained in `STOP.json` and `SHA256SUMS`.

Runtime: CPython 3.14.5 on macOS. `wslc` was not on PATH. No container, Docker engine, game, model, GUI, or shared runtime was invoked. This was a finite, standard-library-only decision-function construction; it does not consume a #59 CPU/Xvfb allocation.

## Controlling stop

The H/T/D/C/U and five-case gate were recorded in Issue #6562 before the candidate run, but exact candidate/fixture/test/runner/auditor hashes were not recorded in a freeze artifact before execution. This fails the provenance gate. The after-run hashes are preservation metadata only; they are not a retroactive freeze. The candidate/auditor outcomes remain observed diagnostics, with overall disposition STOP and no retry.
