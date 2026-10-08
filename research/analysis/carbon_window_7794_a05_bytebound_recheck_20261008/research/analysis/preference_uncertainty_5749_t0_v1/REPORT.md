# Preference uncertainty and constructed preference boundary — Issue #5749 T0

## Result

`PASS_METHOD_SCOPED`. A no-model finite fixture separated all ten frozen cases: explicit ranking acted without a query; ambiguous AB/BA profiles accepted only choice-version-bound answers; minimax-regret selected robust C (worst-case regret 1); an infeasible query without an authorized default yielded; no response and a stale answer yielded; forbidden A was never selected; a constructing preference produced only a scoped selection after neutral explanation; and equivalent-frame answer reversal held with `HOLD_FRAMING_SENSITIVE`.

The independent raw-only oracle agreed on 10/10 outcomes/actions/regrets. Forbidden effects: 0. The independent auditor rejected 7/7 corruption controls. Runner and auditor each ran exactly once after freeze in local Docker.

This is method/fixture evidence only. It is not a human-preference, comprehension, interruption-cost, runtime-safety, or product result. It does not establish the Issue's higher-level comparative hypothesis or authorize actual user questioning or action.

## Freeze and execution

- Issue #5749 freeze: comment 5924422910; premise correction: comment 5924349551.
- Allocation: `5749-preference-gate-t0-20261001-01`.
- Base main: `8827fad422b225bddd9b1c6d34bfa68ca19265c5`.
- Branch: `research/5749-preference-gate-t0-20261001`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Docker Desktop 29.8.0, Linux amd64, network disabled, 1 CPU, 256 MiB, 64 pids.
- Exact commands, exit codes, raw hash, and the pre-freeze construction correction are recorded in `outputs/formal01/execution.txt`.

## Reproduction and retained evidence

`fixture.json`, `runner.py`, and `audit.py` are frozen. Run `python test_preflight.py` as a construction check. Formal allocation output is `outputs/formal01/raw.json`; the independent audit is `outputs/formal01/audit.json`. Do not rerun the consumed allocation. The test suite checks method construction only and does not model a real user.

## Limits and next discriminator

The ranking profiles and utility values are authored finite assumptions. `SCOPED_SELECTION` is an informational, choice-version-bound preference result, not permission; the admissible-effect filter remains separate. Framing stability, honest/comprehended answers, realistic question burden, independently endorsed preferences, and real effects remain unmeasured. Any T1 needs separate explicit study authorization and prospective human/effect scoring; this T0 must not be reinterpreted as such evidence.
