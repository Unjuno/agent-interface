# Issue #6539 construction record — pre-freeze host smokes

**Scope:** implementation plumbing only. These two Windows-host invocations are
not the preregistered T0, not WSLc/container results, and not evidence for H.
Their outcomes are excluded from threshold decisions and formal seed counts.

## Construction seed 6539001

- Candidate exit 0; 2,242 test episodes/arm, 256 training rows/fitted arm,
  40 epochs. Candidate source SHA-256:
  `94bf95f7c1344b21dff5e72bb9f77457e27509706c96ebf4369b9ed43be37f7c`.
- Raw SHA-256: `8678110ca8c91d996b5043c4a1f5c64899587b778b646f187f85fbf34bac26ee`
  (5,608,176 bytes).
- First auditor attempt exited 1 with `KeyError: 'rule'`; retained as a
  construction-code failure. Corrected auditor invocation exited 0 with
  `PASS_METHOD_SCOPED`, integrity/reconstruction only. Auditor SHA-256:
  `cf23211dbc5cdeb4a5f871eb1097c748db39e3cd192ccdf579314037eb5f433a`.
- Audit SHA-256: `eed4a72e5b9f1d603eea11666a26e801423e8a55c5c1a107b2d142ad6dad7c14`
  (2,192 bytes).

## Construction seed 6539002

- Candidate exit 0; same construction budgets. Candidate SHA-256:
  `63306eef9f9a2b0a55b1c2d7978a383cab13a7d3c239bab3ead730a0c693d364`.
- Raw SHA-256: `927a4d873663163a8fd91b5888d90915a6076204008c3bc3a1c0e4b8f92aa42f`
  (5,674,891 bytes).
- Independent auditor reconstructed training rows, transforms, optimizer
  weights, held-out generator, proposals, scores, and denominators; exit 0,
  `PASS_METHOD_SCOPED`, `synthetic_raw_integrity_only`, no efficacy/safety
  claim. Auditor SHA-256:
  `cf23211dbc5cdeb4a5f871eb1097c748db39e3cd192ccdf579314037eb5f433a`.
- Audit SHA-256: `44cb11b1825bbd07a8ab78aac9723414afcb9dd52dade0a803538665c7984e30`
  (2,192 bytes).

The second smoke predates the final review separating pre-action admission from
post-action effect confirmation. It does not validate the corrected protocol.
Both output sets are immutable construction artifacts and must not be pooled
with formal runs.

## Final-protocol construction checks

- Construction seed `6539003` candidate exited 0 (raw SHA-256
  `63cf009cea6f1233b9d2b76be121f25b13c835f5efccce64d06e3011d652d578`,
  5,955,104 bytes). Its first audit failed closed because the test-only seed
  was not in the formal seed schedule. No audit JSON was written; this is
  preserved as a construction gate failure.
- After allowing only the explicitly supplied expected seed in that gate,
  construction seed `6539004` candidate exited 0 (raw SHA-256
  `39fd9c67989ead647b629af9f3aefcf1021ba6bdadaf23ce7a7811b9d697b64e`,
  5,955,093 bytes). The independent audit exited 0 with
  `UNCERTAIN_NO_DECISION_MARGIN`; this is a plumbing/integrity smoke only, not
  a hypothesis test or formal result. Audit SHA-256:
  `58cf0c8466da9b2dd0300744af1e79e05f63449024fa4c7c25522c10c4d76619`
  (16,232 bytes).
- Candidate source at the final construction invocation:
  `25c96a14b8a6366fcaa8fd11e96bf093ead952c4546b1e766cb09efc877799a2`;
  auditor source:
  `d6f0f336184316371c59d7240d16c92ac3b404e2ccbbeefc976b818dd8a7ff08`.

This seed-gate fix preceded the final removal of candidate seed overrides and
the last wording/margin freeze. Construction-04 therefore verifies its exact
source pair only; it is not a hash match for the eventual `FREEZE.json`.

Formal candidate/auditor/container/retry counts remain `0/0/0/0`. No
container, model provider, GUI, GPU, network, user data, or external effect was
used.

## Remaining gates

The implementation and independent construction tests have since been aligned
on pre-action authority/evidence/freshness/target admission versus post-action
effect completion. `FREEZE.json` and `RUN_COMMANDS.md` now pin source hashes and
the WSLc command contract; the formal package is indexed and present on Draft
PR #6697. Before launch, refresh main/Issue/PR/parallel-owner state and the
allocation, re-freeze if any pinned input changed, and require the exact
non-overlapping WSLc assignment. The existing #6539 request remains unassigned.

## WSLc construction-contract revalidation — 2026-10-03

After refreshing `origin/main` to `3946897b559dc20253b6a5dfcf1e000f10966d60`,
the unchanged package tests were rerun in Microsoft's native WSL Containers
(WSLc 3.0.1.0; Linux kernel 6.18.40.1-1) using the already-cached image
`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
(local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`,
linux/amd64, Python 3.12.14). The source directory was bind-mounted read-only;
network was disabled; requested limits were 0.25 CPU and 512 MiB; no GPU,
candidate CLI, auditor CLI, or output artifact was invoked.

Exact command (PowerShell):

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m `
  --mount "type=bind,source=<study-directory>,target=/src,readonly" `
  -w /src --entrypoint python `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  -B -m unittest discover -p 'test_*.py' -v
```

Outcome: exit 0; 21/21 tests passed in 1.996 seconds. WSLc emitted
`Your kernel does not support swap limit capabilities or the cgroup is not
mounted. Memory limited without swap.` Therefore the configured memory value
is not evidence of effective memory or swap enforcement. This is a fresh
containerized construction-contract check only; it neither updates the formal
candidate/auditor counts nor supplies the still-missing coordinator assignment.
No formal candidate/auditor, training, GPU, or retries occurred (still
0/0/0/0).
