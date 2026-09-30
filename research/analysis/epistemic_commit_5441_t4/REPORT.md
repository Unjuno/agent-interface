# T4 result — bounded delivery and transcript-bound ACKs

## Decision

**PASS — preregistered finite-model gates only.** The action-class policy produced zero unqualified one-shot commits, a 100% reduction versus quorum-only's 3,456, and completed all 108 clean bounded-delay cases by tick 7. The independent replay audit matched all 20,736 scenarios / 103,680 policy traces with zero errors. All four corrupted-artifact controls were rejected.

| Metric | Result |
|---|---:|
| Scenarios / policy traces | 20,736 / 103,680 |
| Unqualified one-shot commits: quorum-only | 3,456 |
| Unqualified one-shot commits: K1 / K2 / K3 / action-class | 1,728 / 864 / 0 / 0 |
| Clean liveness | 108 / 108 by tick 7 |
| Independent replay audit | PASS, 0 errors |
| Corruption controls | 4 / 4 rejected |

Action-class safe holds were: votes missing/late 10,368; split evidence version 5,184; stale actuator 2,160; incomplete recipient set 864; expired certificate 644; revoked authority 322; stale/missing current ACK 288; and insufficient knowledge level 216. Hold counts are across all 20,736 cases and are not disjoint policy-level counts.

## Reproduction

Docker/OrbStack 29.4.0, linux/arm64; network disabled; image pinned as `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

The formal candidate was invoked once after preregistration:

```sh
docker run --rm --network none -v "$PWD:/work" -w /work \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python research/analysis/epistemic_commit_5441_t4/experiment.py \
  > research/analysis/epistemic_commit_5441_t4/raw/formal.jsonl
```

The candidate and auditor source hashes, grid, thresholds, and exploratory-disclosure record are frozen in `PLAN.md` and Issue #5441 comment 5912075580. The auditor is a separate implementation and does not import the candidate.

Independent audit and corruption-control commands (each executed once, network disabled):

```sh
docker run --rm --network none -v "$PWD:/work" -w /work \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python research/analysis/epistemic_commit_5441_t4/audit.py \
  research/analysis/epistemic_commit_5441_t4/raw/formal.jsonl \
  > research/analysis/epistemic_commit_5441_t4/raw/audit.json

docker run --rm --network none -v "$PWD:/work" -w /work \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python research/analysis/epistemic_commit_5441_t4/corruption_controls.py \
  research/analysis/epistemic_commit_5441_t4/raw/formal.jsonl \
  > research/analysis/epistemic_commit_5441_t4/raw/corruption-controls.json
```

## Immutable raw evidence

- `raw/formal.jsonl` — SHA-256 `fdea583c0304b3665b5955fec2f9b1899388d6adadc3b9db8468c12ff3dc3f00`
- `raw/audit.json` — SHA-256 `2385070cad731c9f97e6a7b02db20b8167b13b9a0f57c5c0808c07091d864e2b`
- `raw/corruption-controls.json` — SHA-256 `ae63e93b0a1473471043856d7407ff12681428a836874c05c08ab9fd2d6f7fdb`

Mutation controls independently corrupted one scenario, an unsafe-safety flag, an ACK epoch, and the liveness summary; all four were rejected. Raw and audit outputs are retained unchanged.

## Local CI

Passed before push: `research/analysis/check_index.py` (216 retained result directories), its six unit tests, `research/check_workspace_index.py` (146 directories), `.github/check_public_navigation.py` (26 documents / 927 links), and `git diff --check`. The public-navigation script was run on the host because the pinned minimal Python image does not contain Git; the other checks ran locally/containerized as noted in the execution log.

## Interpretation and limits

Within this authored grid, class-specific K1/K2/K3 gates plus current actuator, expiry, revocation, and transcript-hash checks prevented every modeled unqualified irreversible commit without losing any case in the explicitly clean 108-case liveness population. This is not evidence of matched completion over lossy populations, nor does it prove common knowledge, consensus, cryptographic authenticity, clock correctness, or production safety. The finite channel schedules are deterministic; there are no Byzantine actors, clock skew, real transport, retries, or running actuator.

An earlier asymmetric 9,216-case draft was explored before this T4 freeze and is disclosed in `PLAN.md`; it is excluded from this confirmatory decision. Existing T0–T3 records, including the separate T3 transcript-hash experiment, are not altered.
