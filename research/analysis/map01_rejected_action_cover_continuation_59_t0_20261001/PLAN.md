# #59 rejected-action / continuation boundary T0

Status: retrospective bounded construction experiment; **not preregistered** and
not a live allocation. Source base: `73235730af05375fddf3a9d102d30632e7d43af5`.

## H/T/D/C/U

- **H:** An active model response can fail its primary action health-loss bound
  while its distinct `next_cover` bound still passes on the same current typed
  health sample. These contracts can be adjudicated independently without
  granting the rejected primary action any input authority.
- **T:** Six finite cases derived from retained v39 decision 1 (source health
  97; current health 85; action max loss 8; cover max loss 12; cover critical
  minimum 25; maximum evidence age 30,000 ms): exact boundary, one point below,
  one point above, missing health, evidence age 30,001 ms, and source mismatch.
  Candidate computes the two floors separately. Independent auditor uses a
  separately written literal oracle and checks all rows and the no-authority
  invariant.
- **D:** `PASS_METHOD_SCOPED` only if all six literal outcomes match, the
  primary action is rejected in every case, cover admission occurs only in the
  three fresh/identity-matched health cases at or above floor 85, and input
  authority remains false. Otherwise `FAIL_ORACLE_MISMATCH` or
  `FAIL_CASE_INVENTORY`.
- **C:** The cover floor is `max(critical_health_minimum, source_health -
  maximum_health_loss)`. Equality passes. This is a deliberately narrow
  arithmetic contract; source identity, observation freshness and observed
  health are independent hard gates.
- **U:** No policy-command semantics, temporal applicability after primary
  action rejection, enemy proximity/behavior, ammo, navigation, damage
  dynamics, input dispatch, actual release, liveness benefit, survival, kill,
  map exit, model behavior, latency, or integrated runtime behavior is tested.

## Provenance and execution

The v39 controller is SHA-256
`cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`.
Retained source report: `research/doom/results/map01-v39-coast-liveness-live-01/report.json`,
SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`.
Its retention manifest is unchanged. This experiment reads the decision-1
source/current health and validity limits; it does not alter the old report.

The protocol was recorded alongside, not before, the first candidate execution;
therefore this is a construction result, not frozen/preregistered evidence.
The candidate ran twice on host: first before the CLI output-path adjustment,
then once more to generate the retained `candidate_output.json`. Host commands:

```text
python3 -m unittest -v test_candidate
python3 candidate.py
python3 auditor.py
python3 -m py_compile candidate.py auditor.py
```

No container, model, network, GUI, game, or OS input was used. A formal
container/live follow-up requires its own exact owner-bound grant and a new
frozen allocation; this T0 result cannot be upgraded retroactively.
