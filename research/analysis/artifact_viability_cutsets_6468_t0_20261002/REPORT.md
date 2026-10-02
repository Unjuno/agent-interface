# Archival report — #6468 T0 pre-candidate STOP

**Disposition:** `STOP_BEFORE_CANDIDATE_MAIN_ADVANCED`. This is preserved
pre-candidate construction evidence, not a formal method result. The frozen
main SHA advanced twice before the one-shot start gate; formal candidate,
formal auditor, and retries are all 0. Do not re-freeze or retry this
allocation.

The original README, freeze, stop receipt, candidate, auditor, fixture,
construction packets, tests, and SHA256 inventory are retained unchanged.
The first construction packet was independently rejected for an incorrect
spreadsheet formula-range label; the corrected packet is separate. The
construction unit tests exercise only the deterministic synthetic fixture and
must not be read as a formal run, real-artifact usability, route benefit, or
Agent Interface runtime result.

The two construction-packet SHA entries were computed over Windows/CRLF
working-copy bytes. This macOS checkout materializes the same Git blobs with
LF endings: raw hashes therefore differ, while converting LF back to CRLF
reproduces both recorded hashes exactly. The original Git blobs match PR #6487;
no packet was normalized or rewritten.

The later allocation is separately preserved by PR #6495 and reports
`SUBSUMED_BY_12`: strict TaskContract and dependency-ledger decisions matched
on all authored routes. That successor does not rewrite this earlier STOP.
Issue #6468 remains open for any future, separately frozen question; this
archive establishes no real document/spreadsheet, GUI, model, human-usability,
accessibility, efficiency, safety, or product claim.
