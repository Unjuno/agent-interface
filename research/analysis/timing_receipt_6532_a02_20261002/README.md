# Issue #6532 — timing-receipt allocation-02

Successor allocation after allocation-01's terminal host-invocation STOP. Allocation-01 and its raw are immutable. This finite synthetic test asks whether a prospective `[start,end)` window classifier preserves uncertainty and report/execution chronology. It does not replay the preference-choice experiment or recover any historical timestamp.

## H / T / D / C / U

- **H:** A receipt classifier can distinguish in-window execution, pre-window candidate, post-window auditor, report-before-execution, missing offset, reversed interval, unmapped clock, bad hash, and exact boundaries; invalid or ambiguous receipts never become timing-eligible.
- **T:** Ten frozen timestamp rows and four output mutations. Candidate writes only to a required explicit output path; `argparse` handles help before any candidate logic. The separate auditor imports no candidate module. Once an exclusive CPU-only OrbStack allocation is explicitly assigned, run one candidate and then one auditor (only after candidate exit 0) in distinct cached digest-pinned containers; no retries. Read-only source, network none, dedicated writable output.
- **D:** PASS_METHOD_SCOPED only if independent raw audit reconstructs every complete row, both wholly contained valid controls (including exact start) are eligible only for the timing gate, all invalid/missing/tampered controls remain noneligible, four output mutations are rejected, and container cleanup/hash receipts pass. Any unsafe upgrade is FAIL_METHOD. Pre-launch gate failure is STOP with formal invocations 0/0.
- **C:** Fixture timestamps and clock mapping are authored; this measures finite classification only. A digest proves byte identity, not clock truth or signer identity.
- **U:** No historical #6274 execution timing, real-clock accuracy, real allocation governance, model/GUI/task effect, or production result.

## Status

Allocation-02 source freeze is recorded in `FREEZE.json` against current main `2a01df459a488f1e09d20c57afc09ddc683420fd`; the final start gate must still revalidate that exact main, all source hashes, output-path absence, owner release and coordinator assignment. The source package is prospective only: no candidate/auditor formal invocation or container launch has occurred. OrbStack remains occupied by another active worker. Do not start a container until owner release and explicit slot assignment are observed.

## Construction

`python -B -m unittest discover -s research/analysis/timing_receipt_6532_a02_20261002 -p 'test_*.py' -v`

Construction checks may be repeated. They do not count as a formal candidate or audit.
