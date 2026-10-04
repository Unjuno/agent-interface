# Independent raw-result review

Singer 01a10331-fe80-7eb3-95b9-511ce5dd0a56: PASS for scoped
FINDING_PARSE_FAILURE_NOT_SURFACED. Reviewed actual saved errors/rows, nine native
hashes, source/AST, PID linkage, child exits/readers retired, terminal runtime and
audit sequencing. No critical/important discrepancy. Default40s not measured.
Minor: AST dump varies by Python version; actual frozen image runs Python3.12,
and image identity plus version receipt are retained. On host3.14 use show_empty
True to match3.12 AST serialization; source byte SHA is version-independent.
Reviewer did not independently check public prospective timing or exported
transport copies; main verified export/original exact equality separately.
No acquisition/official auditor replay performed by reviewer.
