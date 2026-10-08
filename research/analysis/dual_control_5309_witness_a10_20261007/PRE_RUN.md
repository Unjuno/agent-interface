# Issue #5309 A10 frozen contract

- Allocation: `5309-WITNESS-A10-HOST-20261007`, a new allocation after A09's terminal pre-candidate STOP; A09 will not be rerun.
- Base main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`.
- Runtime: host Python standard library, used because current OrbStack blob inspect/pull fails. This is not a container run, OS sandbox, network isolation, or security boundary. No model, GUI, OS input, GPU, or product runtime is involved.
- Candidate, environment, and auditor are distinct CLI processes and exchange explicit JSON files. This is procedural separation only: all files remain accessible on the host, so oracle confidentiality against malicious candidate code is not established.

## H/T/D/C/U

- **H:** Across three structurally distinct finite directed state graphs, a deterministic witness-aware chooser with a cost budget will complete more cases than lexical generic-IG selection only when its witness-survival prediction is correct and a preserving action is affordable. With a wrong prediction, over-budget preserving action, or no need for a new witness, it must not claim a completion that the observed independent witness does not support.
- **T:** `design.py` creates 132 cases (11 states across cycle-3, branch/merge-4, and regular asymmetric-4 topologies × correct/misspecified prediction × preservation cost 0/1/2 × pre-existing witness absent/present), yielding 264 arm rows. Both arms receive the same admissible actions and equal IG. `candidate.py` selects from candidate-input only; `environment.py` steps the chosen actions using oracle transitions and emits receipts; `auditor.py` independently reconstructs both arms from workload, choices, raw, and oracle. Run each CLI once after freeze. No seeds or stochastic sampling.
- **D:** PASS only if the auditor reconstructs all 264 arm rows with zero errors, proves all three graph degree signatures are distinct, verifies exact policy selection/action admissibility and true transitions, finds no authority grants or false COMPLETE, and confirms the witness arm's advantage is limited to correct/affordable/no-prior-witness cases. Any mismatch is retained as FAIL; no retry. This gate does not test secure oracle isolation.
- **C:** Small hand-authored graph families and deterministic transitions; equal IG and synthetic cost units are imposed; the policy and oracle share authored assumptions; these graphs may not represent GUI dynamics. An existing independent receipt removes the ranking need.
- **U:** No live GUI, natural frequency, model quality, wall-clock latency, calibrated risk/cost, OS-level release, runtime, safety, user, or product benefit. This is only a finite method transfer check, with weaker execution isolation than A08.

## Frozen commands

From this directory, exactly once each and in order:

```sh
python3 design.py
python3 candidate.py candidate-input.json candidate-choices.json
python3 environment.py candidate-input.json candidate-choices.json oracle.json candidate-raw.json
python3 auditor.py candidate-input.json candidate-choices.json candidate-raw.json oracle.json audit.json
```

`design.py` is a deterministic fixture materializer and is permitted only before hashing/freeze. After formal candidate execution begins, do not rerun any command above or mutate any input/output. Retain the first raw/audit bytes regardless of verdict.
