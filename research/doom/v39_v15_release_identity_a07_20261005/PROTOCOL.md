# V39/V15 release identity audit A07

## H / T / D / C / U

**H.** The retained A02 fake-X raw contains two admitted keys and two corresponding per-key release transitions in each of two cases. A03/A06 auditors can accept a release row after the identity of its prior admission is changed. An audit that pairs each release to exactly one earlier admission by `(id, intent_token, owner_id, step, key)` will preserve the unchanged baseline and reject all frozen single/composite identity mutations.

**T.** Re-audit only the retained A02 raw from PR #7926; do not run the simulator, candidate, runtime, GUI, game, or input. Run one A07 audit process and one separately implemented reference audit process. Require two cases/four unique admission-release pairs on baseline; run 14 in-memory mutations (all non-empty subsets of `id`, `intent_token`, and `owner_id`, separately applied to an admission or a release) plus one duplicate-release control. Both implementations must reject every mutation and accept the untouched baseline. A focused test suite is construction validation and is run before the freeze.

**D.** `PASS_AUDIT_IDENTITY_SCOPED` only if the frozen raw and source hashes match, A07 and the independent reference both accept the four unchanged baseline pairs, both reject all 14 identity mutations and the duplicate-release control, and their saved baseline dispositions agree. Any accepted misbinding or baseline disagreement is `FAIL_AUDIT`; provenance or invocation mismatch is `STOP`. No original A02/A03/A06 disposition is upgraded or rewritten.

**C.** The A02 trace is synthetic fake-X instrumentation. The earlier A06 report remains valid within its declared 52 trace/sample checks; this adds a separate admission-to-release identity property. A unique full tuple may be conservative if repeated identical admissions are legal, but the frozen A02 contract assigns one release to each admitted key within a case.

**U.** No real X11, physical key state, application effect, independent useful feedback, latency, recovery efficacy, live threat response, gameplay, or safety is established. The host-only audit does not claim container isolation or resource enforcement. The unchanged original A02 auditor result remains `FAIL`.

## Freeze and inputs

Base: current `main` `aeed696ff756d68497faed39b92e3546cb144972`.
Retained raw: A02 candidate stdout from PR #7926, Git blob `7878e4e6aba0fe7d085f6a1e41192ef120d8b20d`, SHA-256 `0336cfa2eeebbe48ad816168d5466938a936fcf0782211b21847df6c20038596`.
Prior auditor source: A06 `audit_v5.py`, Git blob `c9d27887c3425663ec57ed6099bfc07fcd5c18f4`, SHA-256 `13a09f56278cc2d9ea91c022918d1c900756a0ab2749742c37b7fdf62b13f051`.

A06's raw-only audit is a retained input for the regression characterization. The new A07 implementation and independent reference use the pinned raw data, not candidate-generated output.

## Execution constraints

- Python: CPython 3.11.9 on the task's Windows host.
- WSLc is not invoked because shared-client ownership is unresolved in the current resource history; this pure-JSON finite audit has no container-dependent semantics.
- No network, GPU, external model, GUI, game, input, user data, or shared runtime.
- Candidate/runtime invocations: 0. A07 auditor: exactly 1 invocation. Independent reference auditor: exactly 1 invocation. Retries: 0.
- Construction TDD tests ran before freeze; their source hash is frozen below.

## Frozen commands

```powershell
python -B research/doom/v39_v15_release_identity_a07_20261005/audit.py --input research/doom/v39_v15_release_identity_a07_20261005/inputs/a02_candidate_raw.json --output research/doom/v39_v15_release_identity_a07_20261005/formal/AUDIT.json
python -B research/doom/v39_v15_release_identity_a07_20261005/reference_audit.py --input research/doom/v39_v15_release_identity_a07_20261005/inputs/a02_candidate_raw.json --candidate-output research/doom/v39_v15_release_identity_a07_20261005/formal/AUDIT.json --candidate-source research/doom/v39_v15_release_identity_a07_20261005/audit.py --output research/doom/v39_v15_release_identity_a07_20261005/formal/INDEPENDENT_AUDIT.json
```

The two frozen commands are each run once after `FREEZE.json` is written. If either exits nonzero or any frozen invariant fails, retain that first disposition and do not retry or edit these sources.
