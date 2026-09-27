# Corrected evidence-binding audit successor 02

Audit allocation: `issue3711-downstream-truncation-artifact-audit-v2-02`.

- **H:** The prior v2-01 audit's sole failure was a mismatched provenance field: it compared the experiment's frozen base against the later audit-code base. The actual attempt-directory/copy/recovery evidence may still be consistent.
- **T:** Independently re-read formal-02, v1 audit, formal freeze, and the preserved v2-01 failure. Recompute the entire attempt-directory snapshot, byte-compare actual request/report with published copies and recovery stdout, revalidate the full-accepted JSON and delivered prefix, and verify the complete formal source hash set.
- **D:** One new pinned-image OrbStack Docker container, `linux/arm64`, network disabled; source and formal evidence mounted read-only; separate output mount. The freeze records two distinct base identities: formal base `2dff8085…` and audit implementation base `e6f74d3b…`.
- **C:** PASS only if the two bases are correctly separated, the previous v2-01 failure contains only its recorded base mismatch, all retained bytes and hashes bind to actual `attempt/` files and recovery stdout, and the truncation predicates hold. Otherwise FAIL; no experiment rerun or artifact rewrite.
- **U:** This is a post-run audit only. It cannot establish OS/network truncation or broader caller behavior.
