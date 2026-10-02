# Issue #6222 T1 — retained-outcome eligibility audit

**Disposition: `HOLD_T1_NO_CROSSABLE_PANEL` for the bounded v38/v39 corpus.** This is an eligibility HOLD, not a finding that a production scorer is unreliable and not a T1 method failure. No prior result was changed, and no MAP01/model/GUI episode or scorer replay was started.

## H / T / D / C / U

- **H:** A read-only inventory can establish whether current retained MAP01 records contain an immutable, sufficiently varied panel and independently replayable scoring paths for T1 without a new live allocation.
- **T:** At main `fe37b6913f75706fc6bd536ae3afd6ed6a72b674`, enumerated the two r133 inputs named below; matched every path and declared size in each retention manifest to the Git tree; independently inspected each report and retained audit summary. The synthetic #6222 T0 fixture and #5766 standard deck were excluded. No scoring implementation was invoked.
- **D:** HOLD. The records are present and indexed, but the eligible panel is not: v38 and v39 are two distinct episodes, not the same immutable outcome crossed over evaluator/setup/repeat; both terminal scores have `map_exit=false` and `episode_finished=false`; neither supplies a clear MAP01-positive endpoint or a route-pair ranking. The v39 v2 audit repairs an artifact-count assumption (218 observations, 217 PNGs plus one unchanged-image reuse); it is not another independent scoring run. Existing audits assert `independent_score=true`, but this inventory does not establish a replayable second scorer implementation bound to the same artifact.
- **C:** The saved reports and audits may already encode a useful independent posthoc score, and the raw AIT/PNG traces are retained. That preserves value for the r133 reconstruction, but it does not create a crossed panel or add a positive terminal case.
- **U:** This is limited to these two retained episodes and the named synthetic controls. It does not claim repository-wide absence of other eligible artifacts, validate any oracle, estimate disagreement rates, or establish MAP01 completion/reliability. Manifest paths and sizes were checked against Git tree metadata; binary bytes were not downloaded and re-hashed in this pass.

## Frozen inputs and observations

| Record | Retained inventory | Score/audit |
|---|---|---|
| v38 `map01-v38-integrated-threat-live-01` | 265 manifest entries; all paths/sizes match; 119 AIT and 120 PNG blobs | Audit says `independent_score=true`; no map exit, 0 kills, 0 deaths, reward 0 |
| v39 `map01-v39-coast-liveness-live-01` | 464 manifest entries; all paths/sizes match; 218 AIT and 218 PNG paths | Audit-v2 says 218 AIT observations with 217 PNG artifacts and one unchanged-image reuse; no map exit, 1 kill, 0 deaths, reward 0 |

Freeze and exact Git blob identities: [FREEZE.json](FREEZE.json). The original and corrected v39 audits remain separate and unchanged. This audit invokes neither; it only uses their retained claims to decide whether the next rung is eligible.

## Consequence

Do not spend a live MAP01 allocation or relabel these two episodes as a crossed sample. A successor eligibility check may include other independently retained task outcomes only after it freezes a route-blind inclusion frame and verifies scorer provenance. Any actual same-artifact re-scoring remains a separately frozen experiment.
