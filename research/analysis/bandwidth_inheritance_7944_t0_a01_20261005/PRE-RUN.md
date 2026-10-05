# Issue #7944 T0 A01 — pre-run receipt

- Allocation: `7944-BWI-T0-A01-20261005-01`
- Specific T0 authorization / successor record: [Issue #7979](https://github.com/Unjuno/agent-interface/issues/7979), created before freeze; parent Issue #7944 remains unchanged.
- Pre-run receipt written: `2026-10-05T04:28:25Z`; freeze manifest follows this receipt.
- Base `main`: `6860b585305e539ec93896f5adcbf658cbbd8592`
- Issue #7944: open; targeted branch-name searches for `7944` and `bwi` returned no branches; no comments record an assigned owner/allocation.
- Parallel-path check: the package path `research/analysis/bandwidth_inheritance_7944_t0_a01_20261005/` is unique. Open #59 PRs #7951/#7957/#7965/#7966 were checked; none uses this package path. PR #7966 does touch shared analysis indexes; index/workflow edits are deferred until that shared-file overlap resolves.
- Construction suite: 12 tests passed before freeze; the suite covers all eight finite fixture cases, all three policies, invalid-edge mutations and five raw-trace corruption mutations. Candidate and audit trace reconstructions matched.
- Formal candidate calls before freeze: 0. Formal auditor calls before freeze: 0. Retries: 0.
- Formal raw candidate output present before freeze: no. Formal audit output present before freeze: no.
- Container attempt: OrbStack Docker API available, but image inventory and pinned no-network run fail on containerd blob reads with `operation not supported`; exact hashes and commands are in `ENVIRONMENT.json`. No daemon or image mutation.
- Frozen execution: host-only CPython 3.14.5, deterministic standard-library model; no network, model, GUI, user, OS scheduler, GPU or input action.

The formal boundary is one candidate invocation and one raw-only audit invocation. Do not repeat either. If either fails, retain its first output and open a distinct successor rather than modifying this allocation.
