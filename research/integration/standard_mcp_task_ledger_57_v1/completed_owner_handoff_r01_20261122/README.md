# Normal completion effect handoff R01

Status: `PASS_SYNTHETIC_COMPOSITION_ONLY` on feature branch from current main
`0b97018dd09302c22167ea61759351f24ad3b396`.

## Question

Can the research effect receipt adapter attribute an independently scored task
effect when the public Win32 action completed normally, without a recovery or
cancellation receipt, while preserving the release and late-input-horizon
requirements used by the recovered-action path?

## Change and result

The adapter now has two explicit receipt paths. Recovered actions keep the
existing recovery/cancellation validation. Normal completion requires a
recorded exact `interface_results` lookup and dispatch, matching call,
operation, generation and program expiry, `completion_custody` in the completed
phase, verified empty release, and a generation-bound neutral readback whose
sample count and maximum gap satisfy the recorded horizon. Missing or
contradictory custody fails closed.

The fixture test models a successful final state whose effect interval is after
both the authority expiry and verified neutral horizon. The result preserves
`factual_task_success=true` and reports `timing_status=after_release_horizon`,
while `eligible_task_success=false`. A separate hostile case removes horizon
verification and is rejected. Existing recovered-action cases remain in the
same suite.

The work also exposed and fixed an ordering assumption in the shared timing
adjudicator: on a normally completed action, release can precede lease expiry.
That order is valid. Release must precede the end of the neutral horizon, while
eligibility still depends only on the effect occurring by authority expiry. A
new check confirms an effect after release and before a later expiry remains
`within_authority`; a later effect remains ineligible. Recovery timing and its
existing expiry-before-release cases are unchanged.

On Windows CPython 3.11.9, the focused handoff, reuse-horizon and effect timing
suites pass **26/26 normally and 26/26 under `-O`**. Latest raw output is under
`raw/normal-final.stdout.txt` and `raw/optimized-final.stdout.txt`. Earlier
18-test output from before the timing-order fix is retained as
`raw/pre-ordering-fix-*` and `raw/pre-extra-adapter-case-*`. The first run
exposed an undefined local variable in a test assertion; its failure is retained as
`raw/normal-initial-nameerror.stdout.txt`; after correcting the assertion and
timing contract, both latest runs pass.

## Limits

This is synthetic composition evidence. It used no live GUI, target input,
provider/model request, WSLc, Docker, or resource allocation. It does not convert
R05's independently observed delayed fixture effect into an adapter-qualified
result: R05 lacks a recorded `interface_results` lookup and public pre/post
observation pair, so its raw evidence must remain unadapted. This change also
does not prove that the public runtime itself reports application task success.

## Reproduction

From `research/integration/standard_mcp_task_ledger_57_v1` on the tested source
tree, with Windows CPython 3.11.9 and repository root on `PYTHONPATH`:

```powershell
python -m unittest -v test_effect_receipt_handoff_v1 test_effect_receipt_reuse_horizon_integration_v1
python -O -m unittest -v test_effect_receipt_handoff_v1 test_effect_receipt_reuse_horizon_integration_v1
```

The exact source tree is identified by `source-sha256.txt`; host and command
conditions are in `conditions.json` and `environment.json`. Verify packet files
with `sha256sum --check SHA256SUMS`.
