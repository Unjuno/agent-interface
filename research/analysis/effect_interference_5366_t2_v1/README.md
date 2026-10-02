# Effect interference T2 — Issue #5366

Start with [REPORT.md](REPORT.md), then inspect `FREEZE.json`, `PLAN.md`, and `RUN.md`. The formal candidate raw JSON and independent audit are under `outputs/formal/`; `SHA256SUMS.txt` covers the retained package files. To reproduce the construction suite, from this directory run `python3 -m unittest -v test_construction`. Formal candidate/audit invocations were consumed once and must not be repeated.
