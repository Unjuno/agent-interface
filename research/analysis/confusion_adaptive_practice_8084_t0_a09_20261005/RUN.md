# A09 run record

- Base main: `cc2eb4a205bb8f8001b1baed05f482208c0b0935`; freeze commit: `6f8f3d476c2e229686e5cde22f2249697a761ce6`.
- Exact interpreter: `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe`, CPython 3.12.10.
- Construction: 5/5 normal and 5/5 under `-O`; two pre-freeze assertion wording mismatches retained. Sparse-aware freeze stage/commit succeeded, frozen blob exists in HEAD, package was clean before generator.
- Generator: one invocation, exit 0, ~3.75 s, 80,000 rows.
- Candidate: one invocation, exit 0, ~1.33 s, candidate mount held only candidate.py and observed_counts.json.
- Auditor: one invocation, exit 0, ~37.64 s; the auditor-only truth file was not candidate-visible. Stdout/stderr and exact handoff artifacts retained.
- Audit: 80,000 rows reconstructed, zero base errors, all five mutation controls rejected, 20 gates evaluated, none qualified.
- Full frozen source hashes verified post-run; all package evidence checksums in `SHA256SUMS`.
- No WSLc, Docker, network, GPU, GUI, model, participant, external data, or shared service; no container isolation claim.
