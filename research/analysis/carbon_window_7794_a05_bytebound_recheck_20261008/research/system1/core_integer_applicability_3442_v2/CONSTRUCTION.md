# Construction record

Allocation: `core-integer-applicability-3442-v2-20261001-01`.

Before the one-shot finite run, a host-local construction suite exercised the
current-main validator on nine selected boundary cases, checked the exact
13-field × 15-value × 2-mode matrix shape, and checked the invalid-operation
index. The independent raw-only auditor was separately unit-tested for an
accepted integer, `False` refusal despite `False == 0`, candidate/program
disagreement, and input-byte mutation.

The first construction run exposed two harness faults before any 390-row
matrix was executed: the sparse checkout omitted the runtime source, and a
valid observation sequence of zero was accidentally tested with current
sequence one (which correctly caused a stale-observation refusal). The source
was included in this isolated worktree and the admission control was corrected
to match the program value. A review of the current source also found 13
numeric leaf sites, not the predecessor freeze's stated 12; this is why the
successor expands to 390 cases. The predecessor freeze and branch were not
edited.

After those corrections, **8/8 construction unit tests passed** under CPython
3.13.14 on macOS arm64. This includes a synthetic (non-runtime) 390-row
auditor fixture and ten raw-corruption controls; the candidate validator was
only exercised on the nine selected construction cases. This is not the
formal 390-row result. No candidate matrix or independent matrix audit has run
yet; no container or shared runtime was used.
