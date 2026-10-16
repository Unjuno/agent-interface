# A01 outcome: audit method failure; allocation consumed

Frozen source commit: `24c12c73cf87eb45aeebc62e4e1360cbc74392a0`.

The candidate/runner executed once and produced 61,800 deep-attempt rows across 103 synthetic worlds and three arms. The independent auditor executed once and exited 1 at `sentinel_not_reproducible`, before any scientific decision gate. Static diagnosis found the implementation mismatch: the runner sampled sentinels from eligible-cell generation order, while the auditor sampled from sorted cell IDs. This is an auditor reconstruction defect, not evidence for or against the hypothesis.

A01 is consumed. Do not rerun or repair its output under this allocation ID. The first audit stdout/exit and candidate inputs/outputs are retained byte-for-byte in `raw/`. No mutation-control run was made because the main audit did not pass.

SHA-256:

- `shallow-input.json`: `82b1bfd58d4a3cf169d10a850411a6d13b2d8d2570a567f68a13a1983619f7f5`
- `candidate-allocation.json`: `a3f88c53fc4b31392c7d5e87f802b55774e8e3c55ea699e97c37ba678976934c`
- `candidate-output.json`: `a58a94bb36058ae33643c208cb71a497afaba848bf095fbd8023a5064aa6f824`
- `audit-first-output.txt`: `de2fdfd06c3f54bec7775a6b4c873632ef99263298da60c556bb8a067ea334ac`
- `audit-first-exit-code.txt`: `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`

Scope: offline synthetic method only; no live replay, GUI, model/provider call, WSLc, Docker, or shared runtime.
