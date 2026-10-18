# A08 run record

- Base main: `24cbb631b972eee1723d2372adf53032dfdaab20`; freeze commit: `b670f06816ee5d9690d06acb7eec39a86317e11a`.
- Interpreter: `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe`, CPython 3.12.10.
- Construction: 4/4 tests normally and 4/4 under `-O` before freeze. Freeze staged with `git add --sparse`, committed successfully, verified in HEAD, and package was clean before generation.
- Generator: one invocation, exit 0, ~3.08 s; 80,000 observations; stdout/stderr retained.
- Candidate: one invocation, exit 0, ~0.59 s; candidate directory contained only `candidate.py` and `observed_counts.json`; stdout/stderr retained.
- Auditor: two local filename-order/case preflight checks were rejected before process launch. After comparing the exact filename set, the single auditor process invocation exited 0 in ~22.87 s; stderr empty. Exact observed counts and candidate stdout were handed to a disjoint auditor directory alongside auditor source and scoring truth.
- Audit: 80,000 observations reconstructed; 20 gates evaluated; `METHOD_PASS_SCOPED`; zero base errors; all five mutation controls rejected; two gates meet the frozen all-profile Wilson criteria.
- All source hashes in `FREEZE.json` verified against the frozen source; complete package evidence checksums in `SHA256SUMS`.
- A post-formal construction-only test run failed 1/4 because its initial candidate-directory assertion no longer applies after the fixture is generated; exact output and phase explanation are retained. The pre-freeze tests had passed 4/4 in both modes. No retries or frozen-source edits.
- No container, WSLc, Docker, network, GPU, GUI, model, participant, external data, or shared service. Host process separation is not a container isolation guarantee.
