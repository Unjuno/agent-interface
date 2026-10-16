# Cleanup identity audit and evidence custody — Issue #8681

## Initial counterexample

Synthetic A01, recorded by merged [PR #8682](https://github.com/Unjuno/agent-interface/pull/8682), is `FAIL_METHOD`. Duplicate accepted IDs masked an earlier unmatched acceptance while both `input_terminals_complete` and `input_releases_verified_empty` became true; conflicting duplicate terminal rows made empty-release evidence order-dependent. Four controls passed and three duplicate probes violated the conservative expected gate. This establishes a receipt-reconstruction defect in the synthetic component model, not that duplicate rows occur in production or that physical input was released.

## One implementation path

The broader current cleanup implementation was merged in [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771). It rejects duplicate/orphan identities and malformed event records, requires unique matching accepted/terminal identity sets, and fails closed before release certification. Later synthetic regression work covered malformed accepted tokens and a valid release pair followed by malformed rows; ordinary and optimized test runs were recorded on the issue/PR history. The merged change is still component evidence only: it does not establish physical key state, live-game effect, or #59's separate live threat-control gate.

## Evidence that still needs custody-preserving reconciliation

- [PR #8687](https://github.com/Unjuno/agent-interface/pull/8687) remains OPEN with `DIRTY` merge state. Its head contains 47 A02–A05 evidence files absent from #8771's tree, and the overlapping source/test blobs differ. Preserve the exact original package provenance and reconcile the unique evidence separately; do not apply overlapping cleanup logic a second time.
- [PR #8838](https://github.com/Unjuno/agent-interface/pull/8838) remains OPEN/Draft. Its A07 focused run recorded that current main failed three assertions while the candidate passed five in normal and optimized modes; the raw wrapper's failure-name classifier miscounted subtest failures. The later broader #8771 implementation covers the issue classes, but the evidence packet and test context should be reconciled before discarding its ref.
- Issue #8681 remains OPEN. Its later comments identify #8771 as the single implementation candidate and close duplicate implementation proposals as redundant while preserving their historical artifacts.

## Scope boundary

This is evidence about synthetic cleanup receipt reconstruction and test coverage. It is not physical-release evidence, proof that a live cleanup failure occurred, or permission to run a game/input experiment. Keep one implementation candidate and preserve distinct raw, audit, and source histories when retiring overlapping refs.
