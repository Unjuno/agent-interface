# A03 run record — candidate harness failure

**Disposition:** `STOP_CANDIDATE_HARNESS`; no parity finding. Candidate invoked
once on 2026-10-02 (Asia/Tokyo) using the frozen configuration. Retries: 0.

The R arm exited 1 before evaluating any sample because the R harness treated
the frozen `seed_list` preregistration as a list of case objects and attempted
`case$seed`. Raw error is retained in `output/r.stderr.txt`. No R raw result
was produced. The Python arm completed once with exit 0 and retained six raw
rows in `output/python.raw.json`; that arm alone is not a parity result.
Combined candidate exit record: `R=1`, `PYTHON=0`.

Per the frozen gate, the independent auditor was not run because both
candidate arms did not exit 0. No numerical R/Python comparison is claimed.
This is a protocol/harness failure, not evidence for or against the Python
TailID implementation. A corrected successor must have a new experiment ID,
new preregistration, fresh inputs, additive output path, and preserve this
record unchanged; A03 must not be rerun or repaired in place.

The six seeded input files, source, image and code freeze are retained under
this directory and the parent `crAn_parity_a03_*` files. See `FREEZE.md` and
`SHA256SUMS` for identities and integrity checks.
