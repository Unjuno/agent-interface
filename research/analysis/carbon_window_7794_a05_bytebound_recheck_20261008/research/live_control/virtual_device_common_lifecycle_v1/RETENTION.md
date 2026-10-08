# Retention boundary

GitHub retains the evidence needed to review the scoped result without claiming more than was transferred:

- deterministic pre-measurement `source-freeze.tar.gz` and A2 orchestration freeze;
- `REPORT.md`, `results-summary.json`, final frozen-auditor output and the first namespace-failure audit;
- independent postformal verifier output;
- six corruption-control outcomes;
- explicit A1 infrastructure-timeout record and A1/A2 non-pooling boundary;
- `publication.json` with hashes for the complete local evidence archive.

The complete local archive `virtual_device_common_lifecycle_v1_complete.tar.gz` contains 599 retained files (frozen sources and construction, A1 first outcomes/partial stop state, all 40 A2 first outcomes, Tk/X11 logs, both audit histories and postformal verification). It is 52,151 bytes with SHA-256 `c996533d4e566bd11c1c6a9b04ef2d19405104918c55d35386c59bbf6918beeb`. Fresh extraction verified all 599 manifest entries; rerunning the identical frozen auditor through the read-only A2 namespace view and rerunning the independent verifier produced byte-identical PASS outputs.

An attempted Base64-chunk GitHub transfer was detected before PR publication to be non-byte-exact (two chunks were each one character short). Those broken chunks and their reconstruction script were deleted from this branch. They are not evidence and no GitHub-full-raw claim is made.

A1 and A2 remain separate allocations. A1 has 12 complete first outcomes plus one partial directory and is `STOPPED_INFRASTRUCTURE_TIMEOUT`; none of its outcomes are pooled into A2. A2 has exactly 40 first outcomes, no case reruns or replacements.
