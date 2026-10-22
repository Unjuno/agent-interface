# Issue #8553 A03 — observation-branch audit result

## Disposition

**`CONFIRMED_AUDIT_GAP`.** In a fresh audit-only allocation, the frozen A01 checker accepted both a policy with unsupported observation values (`secret-a`, `secret-b`) and a policy with the correct `red`/`blue` signatures routed to swapped child actions. A separately implemented finite replay accepted the unchanged A01 policy and rejected both mutations. It replayed the two retained policy trees and accounted for all five frozen cases.

This confirms that A01's retained checker did not establish the intended policy-observation binding gate. The original A01 result, raw candidate, saved audit, report, and classification are preserved unchanged; do not cite its historical `PASS_METHOD_SCOPED` as evidence that its serialized branches were constrained to authorized observations. The A01 result may still describe its other finite fixture findings, but this audit-only result does not repair or reclassify them.

## H / T / D / C / U

- **H:** A01's checker can accept unsupported branch values and behaviorally wrong observation routing because it checks `observation_features`, while the candidate stores branch signatures under `observation`.
- **T:** The A01 fixture, candidate JSON, saved audit JSON, and audit source were copied byte-for-byte into this allocation. One diagnostic process applied two in-memory mutations to the frozen A01 input; an independent checker replayed all retained CEGAR policies using only safe selected predicates and the finite transition fixture. No candidate policy was generated.
- **D:** `CONFIRMED_AUDIT_GAP` required the original checker to accept at least one diagnostic mutation, the new checker to accept the unmodified policy, reject both mutations, and account for all five rows. All conditions passed. This is a checker-coverage result, not evidence that the original unmodified policy was wrong.
- **C:** A01's saved policy happens to route `red` to `left` and `blue` to `right`, which matches the fixture. A conservative unknown result or a different policy representation might avoid the gap; neither was compared here.
- **U:** The result is limited to the serialized policies and deterministic authored fixture. No live interface, real observation source, recovery execution, safety outcome, or product benefit was tested.

## Diagnostic outcomes

| Input | Frozen A01 checker | Independent A03 replay |
|---|---|---|
| Unmodified A01 candidate | Pass; exactly matches saved `audit-a01.json` | Pass; 5/5 cases, both recovery policies replayed |
| Replace `red` / `blue` branch values with `secret-a` / `secret-b` | Pass | Reject: policy branches do not cover emitted observations |
| Keep `red` / `blue`, swap their child policies | Pass | Reject: `red` routes to a non-goal successor |

The mutated inputs existed only in memory inside the diagnostic process. They did not replace the preserved A01 candidate or audit. The A03 raw-only replay rejected 2/2 mutation controls.

## Provenance and execution

- Issue: [#8553](https://github.com/Unjuno/agent-interface/issues/8553); predecessor A01 is [PR #8559](https://github.com/Unjuno/agent-interface/pull/8559), merged at `6c153c298ce551b24dc2f0ab645ee54c655217d8`.
- A02 was held before formal execution because `main` moved after its freeze. Its formal candidate, legacy diagnostic, and independent auditor counts remain 0/0/0; it is retained on its branch and recorded on the Issue.
- A03 base main: `9ea5e64a52d2c953e6ea4f649af9e0a8ac1a2407`.
- A03 freeze commit: `73bac300e015f80232506a38f87257d10b62bdba`.
- Freeze SHA-256: `972cdf4ce94a6c2011b946900bc5cf40a8dfc70f24b102894339768206747024`.
- A01 fixture file SHA-256: `514788d1b15a58a08469717370cd062762184cec9119082e5291ff8b66598baf`; its canonical JSON digest bound by the A01 candidate is `3ee208ae8d06e5608206b93be0f996fcc2f81e9ece6beead1d6ae86b69699306`.
- A01 candidate SHA-256: `0bf12edd869f39c7a00338b74597c9264f70a98bd3629a89f9604c0df162622e`.
- Formal run: candidate 0; legacy diagnostic 1; independent auditor 1; retries 0. Both subprocesses exited 0. Exact arguments and timestamps are in `results/RUN.json`; output hashes are in `results/SHA256SUMS`.
- Runtime: host CPython 3.12.13 on macOS 27.0.1 arm64. The audit uses only standard-library JSON and finite transitions; no container, GUI, model, network, user data, or action was involved.

The construction suite passed 3/3 under CPython 3.12.13 and 3.14.5. Construction checks and formal outputs are kept separate in `CONSTRUCTION.stdout.txt` and `results/`.
