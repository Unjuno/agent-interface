# Protocol — Issue #8609 T0 A01

## H / T / D / C / U

**H.** In the frozen finite interface contract, an explicit versioned degradation selector will preserve more correctly supported non-consequential outcomes than an all-or-nothing route under independently removed optional services. It will not enlarge authority, strengthen result claims, discard mandatory release obligations, or admit an operation after any of its required guarantees is unavailable.

**T.** Enumerate all 1,024 combinations of six optional services (`planner`, `raw_observer`, `semantic_observer`, `verifier`, `effect_observer`, `telemetry`) and four independent contract bits (`authority_granted`, `release_channel_available`, `evidence_fresh`, `release_pending`). Compare (A) a binary full-route policy and (B) the versioned operation contract. Candidate and raw-only auditor each run exactly once after source, input, runtime and gates are frozen. The independent auditor reconstructs eligibility, claim ceilings, authority, release custody and pairwise monotonicity without importing candidate code. It also applies six frozen corruptions: omitted requirement, stale-as-fresh, authority enlargement, claim strengthening, hidden fallback, and dropped pending release.

The operations are read-only `read_raw`, read-only `inspect_semantic`, capability-only `admit_reversible_action`, and read-only `verify_effect_evidence`. “Admit” is a contract classification, not an action invocation. No model, GUI, app, OS input, network request by candidate/auditor, external effect, or shared GPU is used.

**Environment.** Construction and formal computation use the same host CPython 3.14.5 and standard library. Before freeze, the authorized OrbStack Docker context and the default Docker context both returned the same containerd content-blob read error while inspecting the available Python image. No image pull, container start, repair, or daemon mutation was attempted. This finite contract calculation does not depend on container semantics; the selected host runtime is frozen explicitly. This is a host-CPU method result, not container evidence.

**D.** `PASS_METHOD_SCOPED` requires: all 1,024 rows independently reconstructed; zero authority inflation, claim overstatement, dropped release obligations, unsupported admissions, or hidden evidence sources; candidate operation sets and claims monotone under capability removal; all six corruptions rejected; and strictly more rows with a supported read-only result under (B) than (A). Otherwise return the corresponding `FAIL_*` or `HOLD_*`; no threshold is tuned after seeing results.

**C.** Binary refusal may be the more appropriate policy for interfaces whose observation channels are not independently trustworthy, and a version table may add complexity without decision value. The authored dependency table may also omit real coupling.

**U.** This is a finite, analyst-authored contract exercise. It establishes no live GUI behavior, policy/runtime safety, task completion, user benefit, service-failure frequency, or cross-application validity. A method pass cannot authorize a runtime fallback or weaken the existing hard gates.

## Frozen operation contract

| Operation | Required available services / predicates | Maximum claim |
|---|---|---|
| `read_raw` | raw observer; fresh evidence | `RAW_OBSERVATION` |
| `inspect_semantic` | raw observer, semantic observer; fresh evidence | `SEMANTIC_OBSERVATION` |
| `admit_reversible_action` | planner, semantic observer, verifier, effect observer; fresh evidence; explicit authority; available release channel; no pending release | `ACTION_ADMITTED` |
| `verify_effect_evidence` | verifier, effect observer; fresh evidence | `EFFECT_EVIDENCE_REVIEWABLE` |

The selector emits mode `FULL_V1` when all optional services are present and hard predicates allow action admission; `CONTROL_CAPABLE_V1` when action admission remains supported despite an unavailable noncritical service such as telemetry; `READ_ONLY_V1` when at least one read/verification operation is supported but action admission is not; otherwise `NO_SUPPORTED_MODE_V1`. A pending release obligation is copied unchanged and blocks new action admission. If release service is unavailable, the obligation remains pending and is never recast as released. Authority is passed through from the scenario and never synthesized.

The binary comparator admits the same operation contract only when all six optional services and all hard predicates are available with no pending release; otherwise it refuses the whole ordinary route. Its emergency release obligation reporting is identical to the versioned arm and is not counted as useful task work.

## Reproduction

From this directory:

```sh
python3 -B build_model.py model.json
python3 -B -m unittest -v test_construction.py
python3 -O -B -m unittest -v test_construction.py
```

After the freeze commit, formal commands are each one-shot:

```sh
python3 -B candidate.py model.json FREEZE.json
python3 -B auditor.py model.json FREEZE.json results/candidate.raw.json
```

Do not rerun either formal command under this allocation ID. The raw candidate bytes must be retained before invoking the auditor.
