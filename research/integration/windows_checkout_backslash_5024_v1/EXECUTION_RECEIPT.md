# Issue #5024 — execution receipt (2026-09-28)

## Decision

**Outcome: `FAIL_WINDOWS_CHECKOUT_REPRODUCED`; repair gate remains unverified.** This records the portability failure and integrity checks, not a successful fix. Do not treat this receipt as `PASS_WINDOWS_CHECKOUT_PORTABILITY_SCOPED`.

## Frozen inputs and independence

- Preregistered commit: `30793b0fcc05bb7d27c4bc1cae2aaf588321262b`.
- Its `results/formal01` subtree tree: `0f153455c8801dbce77c1013ab5a8b9f9f29e367`.
- GitHub readback: the affected subtree SHA, all 48 path/blob/size tuples are identical at the preregistered commit, intake origin/main `ba546e7a91874bb1476262957954679bdd1c932a`, and current main `f11afa4072aa58f34c4526ebebc2dd9bcec1292d`.
- Parallel GPU branches, containers, and formal allocations were not modified or used. This is a Windows checkout portability experiment only.

## Environment and observation

- Host: Windows 10.0.26200.
- Git: 2.55.0.windows.3.
- On clean clone checkout, Git emits `error: invalid path 'research/analysis/gpu_grounding_template_diversity_2912_v2/results/formal01/corpus\\family-XX__variant-Y.png'` for the 48 tracked entries and exits nonzero. The same errors occur with `core.protectNTFS=false` and when using sparse checkout; the checkout validation sees the offending tree entries before materialization.
- A requested checkout to the frozen commit did not move HEAD from the clone's `ba546e7...` origin/main, so preserve the initial attempt as `STOP_BASE_NOT_REACHED`. The reproduction on `ba546e7...` does establish the Windows invalid-path failure for the target subtree because GitHub independently confirms its complete subtree tree SHA is identical to the frozen commit. The strict exact-frozen-HEAD execution gate itself is not claimed passed.

## Retained-byte integrity

- Extracted the 48 source images directly from Git's binary object database; no image was regenerated or edited.
- All 48 observed sizes and Git blob IDs match the preregistered mapping in `PREREGISTRATION.md`.
- Computed SHA-256 for each extracted PNG and compared with `corpus_manifest.json` `png_sha256`: 48/48 match, 0 mismatches. Example family-01 variant-0: Git blob `f29e0cee88bfcf24e8f9216228ee9a32e371282c`, 552 bytes, SHA-256 `74f202663cdf73a26bbe26d4986578f5983cfbe8d8e68175c1ea2826f5693918`.
- The manifest fixes image/content identities, not filesystem path strings. GitHub code search found no tracked source reference encoding the old literal path.

## Stops and unverified work

- GitHub MCP `create_tree` rejected both a null-SHA deletion entry for a literal-backslash path (`GitRPC::BadObjectState`) and an attempted conventional directory entry (`tree.sha ... is not a valid tree`). No commit or ref update was made by those API calls.
- A local Windows sparse-index checkout experiment became slow while expanding the 90k+ entry repository index. The experiment was stopped; no repository branch ref was advanced. The user-provided workspace itself is not a Git checkout. Do not reuse the affected scratch index as evidence of a repair.
- No repaired branch, PR, hosted Windows full-checkout job, or Linux/macOS regression result exists yet. Consequently no file move is claimed and nothing has been merged to main.

## Next safe continuation

Use a Linux container or another POSIX Git host to create a normal commit from the pinned source tree, moving exactly the 48 paths from `results/formal01/corpus\\family-...png` (one Git path component containing the backslash) to `results/formal01/corpus/family-...png`, reusing each original blob SHA. Preserve this receipt and the original preregistration; do not rewrite historical GPU freeze files or their content manifests. Push the additive branch, open a PR, then verify in a fresh Windows clone that ordinary full checkout reaches tests and run relevant platform CI. Require a complete 48-entry old/new/blob/SHA-256 mapping and inspect that no unrelated tree paths changed before marking the portability hypothesis successful.
