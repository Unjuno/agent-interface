# Allocation 02 result — `PASS_METHOD_SCOPED`

## Scope and decision

On this authored finite two-object fixture, the scoped referent-restatement policy reconstructed 7/9 intended objects correctly, returned UNKNOWN for both invalid-evidence controls, and had zero wrong-object outputs. The raw-coordinate baseline had 3 wrong-object outputs; fresh machine rebinding and initial clarification without later re-grounding each had 4. Scoped re-grounding asked on all three declared source-changing events (including one that preserved the target), and asked on neither stable nor zoom-only cases. The independent audit reconstructed every row and arm with zero errors. The four construction mutation checks rejected target substitution, authority laundering, a missing row, and the unmodified control passed.

Disposition is `PASS_METHOD_SCOPED` for protocol discrimination in this authored fixture only. It does not establish that people understand restatements, that real GUI source-generation changes are detectable, that a stable node is unsafe in any actual application, or that the added clarification cost is acceptable. No GUI, model, participant, OS input, application, or external effect was exercised. Allocation 01 remains its separate immutable launch STOP.

## Frozen identity and exact execution

- Allocation: `SHARED-REFERENT-6558-T0-ORBSTACK-20261002-02`.
- Base main: `b538fe9f83a7b3f739887fe500959fd72523c69d`; source-tree commit: `179e98aabcef81e6d50438a5de642c7265e55329`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Candidate container: `2461e357d9b5fa75bfe698494ff98a57fa63884aa3a34856eb4f5255fb88bafb`, exit 0, network `none`, rootfs read-only. It mounted only `candidate.py` and public `fixtures.json` read-only; `oracle.json` was not mounted. Candidate=1.
- Auditor container: `d5de27fb456da0b7ec835b9bc760bb2ee34326b0b80d39261640027c6976277e`, exit 0, network `none`, rootfs read-only. The source/oracle and candidate raw were all read-only; only the audit output mount was writable. Auditor=1.
- Retries=0. No other container was stopped or changed.

Exact commands are retained in `PREREGISTRATION.md`. The candidate stdout is in `candidate.stdout`; independent auditor stdout is in `auditor.stdout`. The raw candidate and audit are retained as separate files.

## Reproduction results and hashes

- Candidate raw SHA-256: `fe44a00cb162721e30cce0d139f2fd5e9e4867fc937b2d0eb90b341ed47ab0ba`.
- Audit SHA-256: `f5a7fe6f5f162143691be41914a609857d77485a6f99ca4bc152b33457c55432`.
- Candidate fixture SHA-256: `d0ee3a67e049805af49e9cb5ead29e0f1652ca2e90829f5d8a1ba63eb693e2f4`.
- Hidden truth oracle SHA-256: `06c240d94b40536e730e8219537534efc55c7a64ccc8c86016b900df493c6226` (auditor only).
- Candidate source SHA-256: `d7be7a1a89b55c227f8bcec16add5e239672e1ef9cb53f6adf0dc016a3450b0b`.
- Auditor source SHA-256: `b6fc8500ca67a2615589aba09ad9a32140ffa6c7ee5b29192e177d44c9509029`.
- Pre-freeze construction suite: 5/5 passed; formal candidate 1/1; independent auditor 1/1; retries 0.

## Next evidence boundary

T1 would need a separately approved, disposable non-sensitive UI and voluntary participant/consent process to test whether real people notice or correct mismatches and whether the added turn is acceptable. This T0 grants no such authority. Before any runtime integration, an integration worker should independently revalidate the raw package and source-bound invalidation semantics.
