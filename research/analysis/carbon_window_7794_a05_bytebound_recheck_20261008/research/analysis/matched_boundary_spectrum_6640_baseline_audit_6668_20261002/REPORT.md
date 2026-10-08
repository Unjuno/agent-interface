# Omitted spectrum baseline audit — successor #6668

## Disposition

**`PASS_ARCHIVE_RECONSTRUCTION` for this post-hoc comparator audit.** The original #6640 allocation remains `FAIL_METHOD`; its threshold and outputs are untouched. This is a deterministic reanalysis of the same authored 8,192-row / 32-seed fixture, not independent data, causal fault localization, or a real-interface result.

## H / T / D / C / U

- **H:** Omitted Ochiai and raw-frequency baselines could materially weaken the apparent matched-spectrum advantage.
- **T:** Compute standard pooled Ochiai, failed-exposure count, and failed-exposure rate on the immutable fixture and hidden injected-fault labels. Reconstruct the original matched, unstratified, first-symptom and deterministic-random methods without importing predecessor code. Preserve missing exposure as missing, and retain the post-failure `render` symptom as a diagnostic column.
- **D:** Require 8,192 unique rows, all 32 seeds and their fault labels; exact per-seed row/attempt-ID inventory; predecessor per-seed ranking/score agreement; and aggregate metric agreement with the committed predecessor audit within absolute tolerance `1e-12`. No new pass threshold is applied and no predecessor disposition can change.
- **C:** Different baseline normalization, tie-breaking, or excluding post-failure symptoms could change ranks. Those alternatives were not substituted.
- **U:** Same authored hidden-fault oracle and only 32 synthetic seeds/six columns. Baseline selection is post-hoc; no independent cohort, live interface, causal effect, or diagnostic utility is established.

## Results

| Ranking method | Mean first-fault MRR | All injected faults in top 2 |
|---|---:|---:|
| Matched risk difference (predecessor) | 1.00000 | 1.00000 |
| Ochiai (new) | 0.96875 | 0.87500 |
| Failed-exposure count (new) | 0.93750 | 0.81250 |
| Failed-exposure rate (new) | 0.93229 | 0.78125 |
| Unstratified risk difference (predecessor) | 0.92708 | 0.75000 |
| Deterministic random (predecessor) | 0.40417 | 0.21875 |
| First-symptom frequency (predecessor) | 0.29167 | 0.00000 |

The strongest omitted baseline, Ochiai, is 0.03125 MRR below matched and 0.125 top-2 fraction lower on this fixture. It does not overturn the ordering, but it is much stronger than random/first symptom. The predecessor's preregistered matched-over-unstratified MRR lift remains `0.0729167`, below its frozen `0.10` threshold; adding stronger baselines cannot repair that failure. Historical #6640 remains `FAIL_METHOD`.

## Integrity and execution boundary

The audit reconstructed all four existing methods and compared every per-seed score/ranking with the committed candidate raw; it then matched all predecessor aggregate metrics to `1e-12`, errors `[]`. Three local integrity tests pass. One initial test assertion failed because pooled Ochiai was incorrectly expected to equal zero from the *matched-stratum* `NO_OVERLAP` condition; `CONSTRUCTION_LOG.md` preserves the failure and correction. The corrected test independently checks the pooled Ochiai formula.

Inputs are pinned by immutable Git blob IDs in `INPUT_MANIFEST.json`; those blobs were rechecked as unchanged on main through `762bb46b5037a2cd4a09672a2e130760a96ff669`. Execution itself read the same blobs from the branch rooted at `20896908089b52db95678626b295219012769627`. No predecessor candidate/auditor, model, GUI, container, or new resource allocation was used. This successor is explicitly a post-hoc archive analysis; its script hash is retained for reproduction but was not a preregistered container freeze.
