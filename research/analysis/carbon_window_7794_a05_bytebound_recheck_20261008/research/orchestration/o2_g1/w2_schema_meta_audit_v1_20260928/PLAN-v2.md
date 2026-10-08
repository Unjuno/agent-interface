# One-shot audit successor v2 — 2026-09-28

Allocation 01 stopped before the auditor began because the tmpfs-mounted Python native extension could not be loaded. Preserve STOP_01 and its empty raw-output directory. This is a distinct successor allocation; it does not overwrite or retry allocation 01.

## H/T/D/C/U

- **H:** The exact W2 schema blob ebc424d2df631aa74c6d9aee4699c595a27ed589 is Draft 2020-12 meta-valid and all eight frozen case envelopes validate. The independent auditor accepts seven schema mutants as invalid and seven instance mutants as invalid.
- **T:** One actual audit run to a new empty results-v2 directory using source/case blobs pinned in PLAN.md, jsonschema 4.25.1 plus the six SHA-pinned Linux wheels, and base image ID sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9. The only change from the failed launcher is explicit `exec` on /tmp tmpfs, preflighted in a disposable no-output container. Network none; root/source/wheelhouse read-only; 0.25 CPU, 256 MiB, 32 PIDs, dropped caps, no-new-privileges; separate fresh writable evidence mount. Capture install/audit stdout, stderr, return code, JSON output, exact source hashes. One invocation; no retries.
- **D:** PASS only on meta-schema acceptance, 8/8 trace instance validation, 7/7 schema mutation rejections, 7/7 instance mutation rejections, and zero source identity mismatches. Otherwise preserve exact HOLD/FAIL. A separate read-only audit container will independently verify the source/evidence hashes and re-run the declared standards checks without importing meta_audit.py.
- **C:** Conformance to the JSON Schema dialect and these eight synthetic envelope instances only. JSON Schema does not express the complete cross-event chronology, lease, causal, or authority semantics; existing W2 verifier/auditor remain a different layer.
- **U:** No cross-clock calibration, physical input, independent live task effect, recovery efficacy, model/GUI/runtime evidence, external Worker return, inherited lease inventory, or Gate-1 completion. This does not authorize W3/W4/formal work.
