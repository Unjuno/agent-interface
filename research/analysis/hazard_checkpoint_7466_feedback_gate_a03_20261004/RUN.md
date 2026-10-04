# A03 formal run record

- Issue: [#7466](https://github.com/Unjuno/agent-interface/issues/7466)
- Allocation: `UNJUNO-7466-A03-ONLINE-EVIDENCE-GATE-20261004`
- Frozen base: `bb3138d019118bf050fe1136a9ba3619146bb46e`
- Freeze: `FREEZE.json`; source/input hashes remain unchanged.
- Runtime: CPython 3.14.5, macOS Darwin 27.0.0 arm64; host-only standard-library run. No container isolation claim.
- Formal invocation counts: candidate 1/1; independent auditor 1/1; retries 0.
- Candidate: exit 0; calibration gate true; 432 episodes; 669,050 streamed ticks. Raw bytes SHA-256 `afaf783f1f8f8e5f7c4ee93661e27f8962a0c883456650531278de901bd3135f` (314,596,618 bytes). Lossless gzip copy is `formal_01/candidate.json.gz` (18,362,497 bytes; SHA-256 `b391bc0edb3799a6ad0badf7b9f2abe23457b55d13277dc51b477b7abdd6cdb7`); decompression reproduces the raw SHA exactly. Retain the uncompressed file locally for direct replay.
- Auditor: exit 0; 432 rows and 669,050 ticks reconstructed; errors `[]`; all four mutation controls rejected; adaptive policy never activated in independent or reversed cohorts; fallback decisions matched the event baseline. Auditor completed 2026-10-05 01:06 local, approximately 3h43m after the candidate output was written.
- Formal disposition: `FAIL_UNSAFE_RESUME`. The six reversed-cohort cost cells each contain 24 incomplete episode×cost rows (24 distinct held-out streams across six cells); exact effects/completion gate therefore fails. Informative cost-benefit gate also fails: checkpoint-cost 4/replay-cost 1 is 6.98% worse than fixed baseline, and 8/1 is 124.11% worse than fixed and 83.37% worse than event baseline. Other informative cells do not rescue the all-cells gate.
- Detailed independently reconstructed metrics: `formal_01/audit.json`; invocation summaries: `formal_01/candidate.stdout.json`, `formal_01/audit.stdout.json`.
- Review follow-up: `replay_audit.py` read the committed gzip without writing the raw candidate and independently reconstructed 432 rows / 669,050 ticks, with zero errors; 144/144 reversed episode×cost rows remain incomplete and the informative all-cell gate remains false. It wrote only `formal_01/replay_validation.json`. This is supplemental post-hoc artifact validation, not an additional formal invocation. The clairvoyant lower-bound diagnostic is withdrawn because its DP allowed zero-cost idle transitions; see `REVIEW_CORRECTION.md`.
- Local checks: `py_compile` over the frozen Python sources; `python3 -m unittest -v test_construction.py` passed 2/2; `research/analysis/check_index.py` passed after refreshing its generated index; compressed candidate integrity and decompressed SHA-256 matched the retained raw candidate.
- GitHub Issue result comment: [#7466 comment 5981953093](https://github.com/Unjuno/agent-interface/issues/7466#issuecomment-5981953093). Repository artifacts are pending batched publication after local CI.

No source, thresholds, seeds, or formal outputs were changed after freeze. The prior A02 STOP and merged A01 evidence remain separate and unmodified.
