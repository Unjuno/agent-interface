# Issue #6532 allocation-01 — STOP before formal container candidate

**Disposition:** `STOP_CANDIDATE_INVOKED_OUTSIDE_FROZEN_CONTAINER_PROTOCOL`.

## H / T / D / C / U

- **H:** A finite timestamp-receipt contract can distinguish wholly in-window execution from pre-window, post-window, contradictory, ambiguous, unmapped-clock and tampered receipts without upgrading uncertainty to timing eligibility.
- **T:** The planned formal design has ten authored cases and four output corruptions; candidate and independent raw auditor must run once each in separate cached-image OrbStack containers, network disabled, read-only source and separate writable output. This allocation did not meet that protocol.
- **D:** No scientific disposition. Candidate raw is diagnostic only; formal candidate/auditor result is unavailable. A fresh, distinct allocation is needed after source freeze and explicit resource assignment.
- **C:** The only produced raw came from local macOS CPython 3.14.5, not OrbStack. The current source was not frozen by a pre-run hash manifest. The helper invocation was embedded in a shell pipeline whose exact process exit status was not separately retained.
- **U:** No clock-truth, historical #6274 execution, production allocation, preference-choice, GUI, model, task-effect, or timing-validity conclusion.

## Exact execution boundary

While intending a non-executing CLI/help check, the command `python3 -B research/analysis/timing_receipt_6532_t0_20261002/candidate.py --help` was issued. `candidate.py` has no argument parser and therefore executed its candidate path, wrote `results/candidate.json`, and printed `{"cases": 10, "status": "CANDIDATE_COMPLETE"}`. This occurred on the host, outside a source-frozen container protocol. The precise process start/end timestamps and direct exit code were not captured contemporaneously. The raw file is preserved unchanged; its SHA-256 is recorded in `SHA256SUMS`.

Counts for allocation-01: host candidate entrypoint invoked 1; formal-container candidate 0; independent auditor 0; retries 0; containers started by this allocation 0. No auditor was run against this raw. Do not rerun or relabel allocation-01. The unit tests import pure classification/oracle functions only and do not invoke either CLI entrypoint.

## Resource state

At the latest read-only check the OrbStack daemon contained `unjuno-native-ci-6092`, mounted to another active worker's rescue worktree. No release or assignment was observed; no container was started for this allocation. The separate default Docker socket and local Podman/nerdctl runtimes were unavailable. Coordination request: #5085 comment #5945709086. Issue gate record: #6532 comment #5945710309.

## Reproduction / verification

- Raw output: `results/candidate.json` (diagnostic only).
- Construction tests: `python3 -B -m unittest -v research/analysis/timing_receipt_6532_t0_20261002/test_timing_receipt.py` — 9/9 passed. This verifies authored fixture logic only; it does not validate the raw candidate invocation or substitute for formal container execution.
- No formal audit, no formal candidate rerun, and no claim of `PASS_METHOD_SCOPED`.
