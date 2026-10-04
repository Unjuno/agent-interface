# Issue #5420 conditional-kernel admission gate — T0

**Result: `PASS_METHOD_SCOPED`.** A preregistered exact finite-channel experiment found that the marginal-only comparator admits the shared-pad second release, while conditioning on the same recipient's prior observation rejects it. The conditional gate admits the fresh-independent-pad and constant-output controls. The raw-only auditor reconstructed all 16 rows across three scenarios with zero errors and rejected all four preregistered corruptions.

The candidate and auditor each ran once in a pinned, network-disabled OrbStack container; exact commands and exits are retained in [`raw/execution_receipts.json`](raw/execution_receipts.json). Source freeze and hashes are in [`raw/freeze.json`](raw/freeze.json); raw candidate and audit are preserved alongside it. Full interpretation and scope boundaries are in [`RESULT.md`](RESULT.md) and the preregistration in [`src/PLAN.md`](src/PLAN.md).

This is evidence for these three exact binary channels only—not an arbitrary-interface ε-DP guarantee, product privacy result, or measurement of UI/timing/consent/multi-recipient behavior. No formal retry was made or is implied.
