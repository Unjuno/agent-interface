# Preregistered T0 — Issue #6435 slack-equivalence method test

## Frozen question and H / T / D / C / U

This allocation tests the Issue's **no-model T0 measurement method**, not whether a model changes its first proposal under urgency. It uses six disposable GUI-like route-choice tasks and a separate finite event ledger. No participant, model, live GUI, repository runtime, network, real deadline, or external effect is involved.

- **H:** A finite all-attempt method can distinguish deadline-invariant feasible choices from genuine slack-sensitive choices, preserve late/abstained/no-response/forbidden outcomes and separate proposal from independently stipulated effect; a planted route-by-deadline rank reversal is detectable without calling the no-interaction null an effect.
- **T:** (1) Six route-choice pairs: two true slack-equivalent controls; one claimed-equivalent pair whose mandatory verification crosses the short deadline; one lease-expiry mismatch; one changed-user-intent mismatch; and one genuine slack-sensitive positive control. Freeze route time, utility/tie rule, safety, verification and lease rules. (2) Eight event archetypes × four cutoffs (no deadline, 5, 7, 20) = 32 offered rows, including correct-fast/late, wrong-fast/late, abstention, no response, delayed delivery, and forbidden effect. (3) Two route-surface panels × 2 routes × 2 deadlines × 2 attempts = 16 rows: one planted rank reversal and one no-interaction null. Independently reconstruct from raw fixtures.
- **D:** `METHOD_PASS_SCOPED` only if all 32 ledger rows and denominators reconcile; phase intervals stay in the declared monotonic domain; correctness is credited only on effect by cutoff, never on proposal; all six pair dispositions match independent route-feasibility recomputation; impossible short-deadline verification yields; the planted reversal and null are both identified; and the auditor rejects four frozen mutations (drop late/abstained rows, substitute proposal for effect, shift a clock domain, accept a false slack-equivalence pair). Otherwise `FAIL_METHOD`. This is not T1 and does not adjudicate model behavior.
- **C:** The finite cards may be too simple to expose prompt framing, model drift, selection or response-time behavior. Utilities, route bounds and truth labels are stipulated. The correctness ledger does not establish that the route oracle is externally valid.
- **U:** No human, model, real elapsed time, GUI, end-to-end route, safety guarantee, causal deadline effect, latent cognitive mechanism, or human-tempo claim. A positive T0 means only that this measurement protocol distinguishes its planted cases. T1 requires a separate collision-free frozen model allocation.

## One-shot execution and provenance

- Intake `origin/main`: `eacb1346866f660d9d34eb36cd9691fd8184e5ff`.
- Normative Issue #6435 body SHA-256: `1595973b983c2ed86cc316ddd57e68e081b203d3423c572e6a66fe4079fbce96`.
- Runtime: local OrbStack Docker engine, image `python:3.12-slim`, immutable local image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; network disabled, 1 CPU, 256 MiB, 64 PIDs, read-only container root, no capabilities, no-new-privileges. Fixture/source mounts are read-only; only `run/` is writable.
- Construction gate is not formal evidence. Formal cap: candidate once; only if exit 0, independent auditor once using fixture and candidate bytes. No retries.
- Exact frozen input, source and test hashes are in `FREEZE.sha256`; run artifacts and portable checksums are recorded beneath `run/`.
