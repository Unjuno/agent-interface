# Cleanup identity audit and evidence custody — Issue #8681

## Initial counterexample

Synthetic A01, recorded by merged [PR #8682](https://github.com/Unjuno/agent-interface/pull/8682), is `FAIL_METHOD`. Duplicate accepted IDs masked an earlier unmatched acceptance while both `input_terminals_complete` and `input_releases_verified_empty` became true; conflicting duplicate terminal rows made empty-release evidence order-dependent. Four controls passed and three duplicate probes violated the conservative expected gate. This establishes a receipt-reconstruction defect in the synthetic component model, not that duplicate rows occur in production or that physical input was released.

## One implementation path

The broader current cleanup implementation was merged in [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771). It rejects duplicate/orphan identities and malformed event records, requires unique matching accepted/terminal identity sets, and fails closed before release certification. Later synthetic regression work covered malformed accepted tokens and a valid release pair followed by malformed rows; ordinary and optimized test runs were recorded on the issue/PR history. The merged change is still component evidence only: it does not establish physical key state, live-game effect, or #59's separate live threat-control gate.

## Issue and evidence disposition (2026-10-19)

- Issue [#8681](https://github.com/Unjuno/agent-interface/issues/8681) is **closed as completed** (2026-10-18 16:14:52 UTC) for its stated synthetic cleanup-identity defect: the counterexample was retained, the broader fail-closed implementation was merged as #8771, and subsequent current-main regressions covered the malformed identity/token cases recorded in the issue. The closure comment is [#6252155468](https://github.com/Unjuno/agent-interface/issues/8681#issuecomment-6252155468). It does not close #59 or claim physical input release.
- [PR #8687](https://github.com/Unjuno/agent-interface/pull/8687) remains OPEN. Its current head `6195600931fa6de4ecf1a5012cb83b549addb5af` has 49 changed files, including 47 A02–A05 evidence files absent from #8771's merged tree; its overlapping source/test blobs differ from the merged implementation. Do not merge duplicate cleanup logic. Keep the PR/ref until the unique packages are reconciled or an explicit owner confirms another durable custody path.
- [PR #8838](https://github.com/Unjuno/agent-interface/pull/8838) remains OPEN/Draft at head `810fdcfe558ad700f779aaa66c111a4cc19eb9e4`. Its A07 focused run recorded that frozen current main failed three assertions while the candidate passed five in normal and optimized modes; the raw wrapper's failure-name classifier miscounted subtest failures. Preserve its packet and reconcile its test context before retiring the ref.
- The implementation in [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771) is merged at `8af95598a2517088203be2696b043ef329ba5b5c` (merge commit `d82033921f9c2cd5a4c27f9971c46ffa0e781fb2`). It is the sole implementation path. Main's current SHA at this audit is `4e36e47a690621a658515b5107cce020dfe6df82`.

The Issue disposition and the remaining evidence-PR custody work are separate. Closing #8681 records that its defect/fix scope is complete; it does not authorize deleting branches or losing the additional A02–A07 evidence.

## Scope boundary

This is evidence about synthetic cleanup receipt reconstruction and test coverage. It is not physical-release evidence, proof that a live cleanup failure occurred, or permission to run a game/input experiment. Keep one implementation candidate and preserve distinct raw, audit, and source histories when retiring overlapping refs.
