# V3 auditor repair and replay

V1 remains unchanged and failed before case evaluation on the freeze schema key. V2 remains unchanged and its exit-2 report is preserved. V3 corrects two audit semantics: prediction-only is an intentionally unsafe comparator, so its expected mandatory-cue misses are measured rather than treated as audit-integrity errors; optional changed-forwarding metrics count only scorer-oracle IRRELEVANT cases. It remains an independent raw reconstruction and mutation audit and does not change candidate, inputs, thresholds or decisions.

The persisted V3 auditor was replayed once against the retained candidate raw output. See results/AUDIT_V3_REPLAY.txt for hashes and results/audit_v3.json for exact output. Candidate was not rerun. This result is a synthetic deterministic raster method pass only.
