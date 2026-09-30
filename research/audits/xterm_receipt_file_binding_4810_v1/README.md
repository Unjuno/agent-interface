# Issue #4810 — frozen XTerm receipt-file audit probe

This package tests the previously reported receipt-deletion audit gap against
the complete, publicly retained `construction-02` bundle at frozen source
commit `53060eb8c12efdf14a83d0f88969ec93126af0b9`. It does **not** claim to
reproduce the uncommitted `construction-29` copy cited in the #4448 review
comment, and it does not run Xvfb, XTerm, XTEST, or any formal timing actions.

`probe.py` invokes the frozen `audit.py` unchanged on one untouched copy and
three disposable copies, each with exactly one receipt/effect file deleted.
The independent `independent_audit.py` rechecks the baseline, provenance, copy
manifests, and the decision for each condition without importing the frozen
auditor or probe code.

The local Docker image is pinned by immutable image ID in `FREEZE.json`. Inputs
are mounted read-only; only a separate output mount is writable. This is an
offline audit-adequacy check, not an XTerm performance or product result.

To rerun from a checkout containing this directory and the historical source
commit, mount the source `construction-02` directory at `/src/construction-02`,
the frozen `audit.py` at `/src/audit.py`, and a fresh output directory at
`/out`. Run `python3 /code/probe.py --evidence /src/construction-02 --audit
/src/audit.py --out /out/report.json`, then
`python3 /code/independent_audit.py --evidence /src/construction-02 --probe
/out/report.json --out /out/independent-report.json`. The frozen commands are
offline and CPU-only; do not substitute formal runner commands.
