# V39 legacy App Server turn/steer A01

## H / T / D / C / U

- **H:** On Codex CLI 0.146.1, `turn/steer` with the required active `expectedTurnId` can deliver a fresh observation text and image to a follow-up Responses request on that same turn.
- **T:** Freeze the exact local CLI path/version, both generated request schemas, the retained sequence-200 PNG, probe, and tests. Hold the first loopback Responses request open; after its active turn begins, send one `turn/steer` carrying the exact observation text and PNG, wait 2.0 seconds for request 2, then release request 1. Invoke one candidate only.
- **D:** Delivery passes only if the actual `turn/steer` response returns the original active turn ID, request 2 contains the exact observation text and PNG data URL, the original turn completes, and the mock server has no errors. Request ordering is classified against the first response's completed-write timestamp. A coherent failure/STOP remains evidence; no retry or fallback shape is authorized.
- **C:** This is a local App Server test using Codex CLI 0.146.1, a temporary `CODEX_HOME`, and an HTTP mock bound to `127.0.0.1`. The endpoint performs no inference and no game, GUI, or input process is contacted. The retained PNG is used only to test serialization.
- **U:** Even a delivery PASS would establish only protocol compatibility for this local CLI. It does not establish which CLI runs on the target game host, whether user-message steering is appropriate for the production tool-output contract, model comprehension, changed action selection, cancellation/release, useful feedback, recovery, task effect, or live threat exposure. Issue #59's live gate remains open and the private lane is unassigned.

## Why this successor exists

The CLI 0.146.1 `ClientRequest` schema has `turn/steer` with required `threadId`, `expectedTurnId`, and `input`; it has no `turn/start.toolOutput` field. The CLI 0.160.0 schema adds `turn/start.toolOutput`. PR #7973's 0.146.1 experiment tested the latter shape and found the observation was not delivered. This candidate tests the older version's declared same-turn steering route without assuming it will work.

The generated schemas are retained under `schema/`. `FROZEN.json` binds their hashes and the one-shot command. Candidate stdout/stderr, command, exit code, raw mock request bodies and request-body hashes, unit-test output, and audit output are retained under `results/`.

## Candidate result

The one frozen candidate passed on Codex CLI 0.146.1. `turn/steer` returned the same turn ID as the initial active turn. No second Responses request arrived during the 2.0-second pending window. After the first mock response finished writing, request 2 arrived 167.593 ms later with the exact observation text and retained PNG data URL; the turn completed and the mock server had no errors. The candidate exited 0.

This shows the older CLI can queue this text+image input on the active turn through its `turn/steer` route in the mock setup. It did not preempt the held Responses call: the observation appeared only in the follow-up request after that call completed. The route encodes the observation as normal user input, so production equivalence to the newer `toolOutput` route remains untested.

## Verification

- `python3 -m unittest -v test_probe` — 9 tests pass.
- `python3 -m py_compile probe.py test_probe.py audit_result.py` — pass.
- `python3 audit_result.py` — `PASS_RETAINED_TURN_STEER_RESULT`; raw HTTP body hashes and decoded JSON match, and the 0.146.1/0.160.0 schema difference is checked.
- All files listed in `SHA256SUMS` verify.
- `git diff --check` — pass.

The first audit attempt is preserved as `audit-v1.*`. It incorrectly compared `/opt/homebrew/bin/codex` with its resolved Caskroom executable path. The corrected auditor compares canonical paths; the candidate was not rerun.
