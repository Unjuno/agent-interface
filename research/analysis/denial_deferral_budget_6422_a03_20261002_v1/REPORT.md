# A03 result — single-use deferral evidence

**Disposition: `PASS_METHOD_SCOPED`.** The independent auditor reconstructed all 9/9 frozen cases, reported zero discrepancies, and rejected all five preregistered corruption controls. The formal candidate ran once; the independent auditor ran once; retries: zero.

The unbounded comparator issued a fresh request on the same satisfied deferral receipt even when the request ID and presentation scope were changed. The bounded rule returned `HOLD_EVIDENCE_ALREADY_CONSUMED` for that replay, allowed the first use of a distinct unused receipt, and enforced the separate per-scope cap. Safety release remained available at the cap. Bounded repeat presentations: 0; same-receipt replay holds: 1; bounded first-use presentations: 2; effect authorizations: 0.

This addresses the specific one-use replay gap identified after merged PR #6473, on these authored deterministic records only. It is not implementation evidence about a deployed agent, a human-burden/coercion result, or a safety guarantee. Issue #6422 remains open: A01, A02, the 20-case matrix and A03 are separate, scoped records; this does not establish full T0 or authorize T1. No model, person, GUI, live approval, effect, container, WSL, GPU, or CUDA was involved.

Exact preregistration and frozen source hashes are in `PREREG.md` and `FREEZE.sha256`; formal invocation times, exit codes and output hashes are in [`run/RUN.json`](run/RUN.json). Raw candidate JSON and the unedited independent audit are retained in `run/`.

