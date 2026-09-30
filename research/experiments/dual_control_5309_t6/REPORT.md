# Issue #5309 T6 — probe failure and fallback boundary

## Status

`PASS_T6_INDEPENDENT_FINITE_ORACLE` for a synthetic finite policy model only.
This is not a live GUI allocation, a calibrated risk estimate, or a runtime
safety claim.

## H / T / D / C / U

- **H:** When a dual-purpose probe is failed, unknown, or stale, a task-action
  fallback can reintroduce wrong-target effects; yielding instead preserves
  safety in the finite model. Probe information must never override stale,
  failed, unknown, over-budget-harm, or over-cost gates.
- **T:** Exhaustively enumerate target A/B, probe state VALID/FAILED/UNKNOWN/
  STALE, probe cost 0/1/2, expected harm 0/1/2, harm budget 0/1/2, and fallback
  YIELD/TASK. Score effects independently of the decision policy.
- **D:** PASS only if every finite row matches an independently represented
  oracle, no invalid/over-budget/over-cost probe is selected, and authority is
  never granted by this policy. Report wrong-target outcomes by fallback arm.
- **C:** The fallback-policy choice is a cost/safety trade-off; hand-set values
  do not establish real probe reliability, harm, or expected utility.
- **U:** No GUI, model, calibrated probabilities, real effect receipt, timing,
  hidden state beyond target A/B, or process/runtime behavior is covered.

## Frozen execution

- Main read at initial intake: `55c467786b3b98e5f8d1746f9c2970b7ada8b47c`.
  GitHub main moved during intake; an API lookup saw
  `59ffec5d551b0adcf11057eee6da814237a748c8`, then a successful fetch obtained
  `e9742ae867addd1b78fac65fa48650b52bee3b97`. The source branch was created
  from that exact fetched main commit. A local checkout index lock prevented
  materializing the worktree, but this T6 is a standalone
  additive artifact and does not depend on repository source files; intake was
  initially against the 55c4677 snapshot.
- Image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Candidate invocation: exactly once, `docker run --rm --network=none --cpus=1 --memory=256m --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src=<scratch>,dst=/work,readonly <image> python /work/candidate.py`.
- Independent audit invocation: exactly once in a separate network-disabled,
  read-only Docker container with 128 MiB memory.
- Candidate SHA-256: `ba2596c104784136ac11a36e8cbf9e658f042252b12b6c3283880549ae3ad8c5`.
- Auditor SHA-256: `dce1416b4ca42e6bf0ef847aa9c4aa42a4e8fe415571401d683257cd97adbae5`.
- Raw JSON SHA-256: `0b93411768024bd62f035422ec9bf613e15f89b905347c104f735aa45bf4847e`.
- Semantic payload SHA-256 (independently recomputed):
  `a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193`.

## Result

The candidate enumerated 432 rows across the complete finite Cartesian input
product. The independently authored oracle matched all 432 rows and confirmed
432 unique input cases, zero authority grants, and zero PROBE decisions for
invalid, stale, over-harm-budget, or over-cost inputs.

Among the 54 failed-probe cases in each fallback arm:

- `TASK` fallback committed action A in all 54 rows and produced 27 wrong-target
  outcomes (the hidden target was B).
- `YIELD` fallback produced no effect in all 54 rows and produced zero
  wrong-target outcomes.

This is the expected result under the hand-authored outcome model. It supports
the narrow claim that fallback policy is a first-order boundary in dual-control
experiments; it does not say which fallback has higher real-world utility.

## Retained local artifacts

- `candidate.py`
- `raw.json`
- `audit.py`
- `independent-audit.json`
- `SHA256SUMS.txt`
- `docker-invocations.txt`

The scratch files are intentionally retained; no prior Issue results were
modified or rerun.
