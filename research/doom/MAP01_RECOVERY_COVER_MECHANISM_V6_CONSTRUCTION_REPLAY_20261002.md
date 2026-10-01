# MAP01 bounded-recovery v6 construction replay (2026-10-02)

## H / T / D / C / U

**H.** V6's frozen pre-formal boundary repair and inherited v5 event-preservation behavior satisfy their deterministic source-order, event-routing, audit-semantic and pair-summary binding tests on this checkout. This tests the construction gate only; it does not test recovery efficacy.

**T.** From current `main` `14b81dd1f6853623a694266b98538f812847257a`, run the unmodified retained scripts on host CPython with no model/game input:

```powershell
python research/doom/test_map01_recovery_cover_mechanism_v6.py
python research/doom/test_map01_recovery_cover_mechanism_v5.py
python research/doom/test_audit_map01_recovery_cover_mechanism_v5.py
python research/doom/test_audit_map01_recovery_cover_mechanism_v6.py
python research/doom/test_audit_map01_recovery_cover_mechanism_v6_bound.py
```

These tests were each invoked once on 2026-10-02. Results: v6 source/boundary 3/3 PASS; v5 event routing 4/4 PASS; v5 audit decision semantics 3/3 PASS; v6 boundary audit 3/3 PASS; v6 six pair-summary bindings / six one-value mutations rejected. No test was retried. The test files create their own temporary directories where applicable and retain no formal output.

**D.** Construction replay passes only when all five invocations complete with the counts above; a boundary-order assertion, unmatched-event retention, valid-result mutation, missing summary, wrong phase, or any of six unequal arm/summary values must fail. V6's boundary audit preserves the valid frozen PASS label, rejects a wrong phase for all six arms, and rejects missing summaries. The separate v6 bound mutation test rejects each of six changed bindings. This is not a formal allocation result and cannot change v5's invalidated disposition or authorize v6's workflow.

**C.** These are deterministic authored tests, not an independent implementation of the live runtime, clock, X server, game, or scorer. They can pass while untested integration defects remain. The Windows host result does not establish container reproducibility.

**U.** No v6 workflow was triggered; formal arms, container, model, GUI, game, GPU and input invocations were all zero. Docker Desktop's daemon did not return `docker info --format '{{.ServerVersion}}'` within 10 seconds in this session. Docker service/process inventory was not altered. No shared container or scarce CPU/GPU slot was claimed. The formal allocation remains unconsumed and unauthorized; a global owner/slot grant is still required. This replay establishes neither physical occupancy nor bounded-recovery benefit, useful feedback, survival, MAP01 progress/exit, frontier-model efficacy, human tempo, or product performance.

## Frozen input identity

- v6 runner blob: `10344582ffa2ce339bc48dd8d680512a71f4eddc`
- v6 source regression blob: `8bc6190ebfd06ad55feca3ed1c09e0f104f37a6b`
- v6 boundary audit blob: `f9c79f4ebe16d5722863f2d4dcb53b0392f55d76`
- v6 preregistration blob: `c8cd4193771d83a0d3ff112dd9c99b8e9664e3c1`
- v6 boundary audit regression blob: `acb08cac77d3dcc82a2535018d24b32308545d56`
- v6 six-binding mutation regression blob: `c160c6d03272de4c6521b3fdd3676df2ef16cdc1`
- v5 event-routing source blob: `f1b5488f6a039c60afc2af5c7a4e86de8773ecd0`
- Environment observed: Windows PowerShell, Python 3.12 (host, CPU-only); Docker engine unresponsive; source tree clean at test time.

## Relationship to the frozen allocation

This is an additive deterministic construction-test receipt for the already frozen v6 code. It neither edits the preregistration, reruns v5/v6 formal work, nor consumes the frozen global live allocation. V5's posthoc-invalid planner window remains invalid; v6 remains pre-formal pending its exact owner/resource gates. Keep all existing v5/v6 evidence unchanged.
