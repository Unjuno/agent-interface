# Issue #6561 adversarial receipt mutation T1

Status is assigned only by the retained `RESULT.json`; this package is an isolated host-only boundary experiment against PR #6568's frozen candidate and raw auditor, not a WSLc allocation or live-control result.

## H — Hypothesis

The submitted independent raw-only auditor must reject a soft-event packet if (a) both the packet's binding and its event binding are changed together, or (b) the raw guard receipt contradicts the pinned v2 guard semantics.

## T — Test

On the separate, unchanged PR source snapshot at head `b45f6182a4735046a2be837e2c65c4a36dfb1ad8`, produce one valid six-case control packet and four one-case mutations. The mutations are: rebind both `case.binding` and `ONE_SOFT.raw_events[-1].signal.binding`; set `grants_input_authority=true`; set `requires_new_decision=true`; set `keep_existing_policy=false`. For each packet, regenerate the candidate context/prompt and invoke the frozen auditor once as a separate CPython subprocess. The frozen v2 guard defines a valid `SOFT_CHANGED` receipt as keeping the existing policy, not requiring a new decision, granting no input authority, preserving/reducing authority only, identifying a semantic change, and verifying no task success. The predeclared criterion is control accepted and all four corruptions rejected.

## D — Decision rule

Any corrupted packet accepted by the target auditor is `FAIL_TARGET_AUDITOR_ACCEPTS_MUTATION`; all corruptions rejected with the valid control accepted is scoped PASS. The separate post-run auditor validates source hashes, exact mutation deltas, and subprocess outputs without importing candidate code.

## C — Costs and limitations

Five finite packet audits on local CPU only. No WSLc/container, GUI, game, model, GPU/CUDA, network activity by the experiment, or user task input. This tests the construction packet/auditor boundary only; it does not prove a production caller is exposed, live planner behavior, or gameplay effect. The frozen snapshot is a draft PR source, not current-main runtime.

## U — Unknowns

Whether the production caller binds the expected session outside this packet; whether its caller rejects contradictory guard receipts; and whether any issue changes a live model decision. This T1 does not consume or replace #6561's separately gated WSLc candidate/auditor allocation and does not close #59.

## Reproduction

Use Python 3.11 or compatible. From this directory:

```powershell
python -B .\run_probe.py .\results\t1-20261002-01
python -B .\audit_probe.py .\results\t1-20261002-01
```

The runner refuses to reuse an existing output path. `T1_SPEC.json` and `PRE_RUN_SHA256SUMS` were frozen before execution. Retained outputs are `results/t1-20261002-01/raw_packets.json`, `target_auditor_outcomes.json`, `environment.json`, and independent `RESULT.json`. Frozen candidate, auditor, guard and v30-audit hashes are recorded in the spec and pre-run manifest.
