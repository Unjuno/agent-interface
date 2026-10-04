# Independent saved-evidence review and executor qualifications

Boole reviewed first archive commit 5817317a360a483fa862f0ce5fb0ea0835549d22 read-only: 55 files, original manifest 54 targets, freeze 18 targets, saved reconstruction, eight rejection controls and 13 tests. Verdict: archive eligible subject to explicit qualifications and parent integration gates; not production approval. Critical 0, Important 2, Minor 1.

## Important findings (original evidence remains immutable)

1. The frozen auditor does not validate operation names or target/parent/sibling request paths. Invented operations and replacement window IDs were accepted on copied logs. Acquisition negative/reversed clocks were also accepted. Packet expectations are not independently authenticated native request/response provenance.
2. The frozen auditor does not enforce acquisition, mutation, reacquisition order, serial call order, or elapsed time containing call span. Copies moving reacquisition before mutation and zeroing elapsed time were accepted. Actual original saved rows satisfy the supplemental structural checks.

`checks.py` is an additive postrun saved-data checker, not a repaired formal auditor. Five copied-log controls accepted by the original are rejected here; 21 original rows pass. Parent/sibling IDs are inferred from the frozen renderer's consecutive resource allocation, not retained QueryTree response provenance. This cannot detect coordinated forgery or authenticate origin. The first unsuccessful control-construction probe and its regression are retained in FIRST_PROBE_FAILURE.json. No native or formal auditor rerun occurred; the first scientific FAIL remains unchanged.

## Minor reproducibility finding

Default host python3 lacks Pillow. Reproduction used `/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` (Python 3.12.14, Pillow 12.3). Original pinned container uses Python 3.12.3. Run `python3 -B -m unittest discover -s saved_review -p test_checks.py` from this package with that dependency-equipped interpreter. Do not rerun run_saved_checks.py to overwrite its exclusive-created receipt.

## Executor rulings on unverified boundaries

- Native truth: reviewer used saved evidence only, no independent fresh native execution.
- Adversarial isolation: renderer and oracle share a process; no coordinated-forgery protection or blinded oracle.
- Raster authenticity: shape/hash/equality checks do not certify the authored drawing; consistently substituted raster copies can pass. Only scoped identical-patch comparison is claimed.
- Coherence: fixture UUID and quiescent private acquisition do not certify arbitrary writers, loss recovery, currentness, or OS-authenticated epochs.
- Task benefit: no model learning, unaided cue discovery, production resolver or task utility. Explicit-cue FRESH is information-matched and identical to MEMORY.
- Cost: wrapper method counts exclude implicit Xlib transport; serial timings are not causal latency ranking, token costs or end-to-end memory savings. Cold acquisition is separate.
- Cleanup: successful observed key/button 1–3 neutrality does not certify exceptional cleanup or every pointer button.
- Resource state: parent verified own VM stopped and own Engine zero running; shared physical host/kernel means no CPU/security exclusivity. Reviewer did not independently attest allocation.
- Publication: first archive Git push and MCP readback verified by parent. Two distinct comment writes received secondary-limit HTTP 403; no identical write retries, PR creation or merge. Main does not yet contain this experiment. Core quota is not evidence of secondary clearance.
- Parent-only integration checks: workspace 22, scorer 2, namespace 157 checks were parent checks, not reviewer claims. Reviewer independently exercised package 13 and saved evidence only.

Scientific interpretation stays FAIL_SINGLE_CUE_IDENTITY_SAFETY: single selected cue makes three wrong identity bindings in the contradictory fixture. This is an authored counterexample, not a production defect/prevalence estimate. Reduced packet bytes do not establish safe benefit. Supplemental PASS does not regrade the first FAIL.
