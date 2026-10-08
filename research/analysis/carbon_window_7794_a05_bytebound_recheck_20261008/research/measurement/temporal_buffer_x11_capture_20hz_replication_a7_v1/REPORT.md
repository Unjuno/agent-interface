# A7: 20 Hz capture-cost replication — first outcome

Issue #1093. Task `TEMPORAL-BUFFER-X11-CAPTURE-20HZ-REPLICATION-20260918-007`.

## Decision

**REPLICATE_20HZ_COST_PASS_SCOPED**. The actual container supervisor completed six fresh counterbalanced pairs / twelve private Xvfb+Tk sessions in one formal invocation. Reruns, replacements and post-result tuning: 0. Workspace `/mnt/data/experiment_1093_a7` is outside a repository checkout. No shared runtime/workflow, task input, model/provider inference or user data was involved.

H: the retained #1061 20 Hz overhead rejection would recur. It did not recur in this block. Preserve every predecessor outcome; no pooling or retrospective relabeling.

T: identical measured predecessor code and fixture; 320x240 private display; no-capture baseline versus 20 Hz full-frame raw XGetImage; 500 ms ring; 300 ms warmup; 1500 ms nominal measured window; six alternating-order pairs.

## Measurements

| Pair | Capture p95 ms | Runner CPU % | Callback-count ratio | p95-gap increase ms | Max-gap excess ms |
|---|---:|---:|---:|---:|---:|
| 1 | 1.238021 | 2.166420 | 1.000000000 | 0.012604800 | -0.029996 |
| 2 | 1.204666 | 2.101274 | 1.000000000 | 0.031578000 | 0.019829 |
| 3 | 1.313229 | 2.189233 | 1.010752688 | 0.038616100 | 0.165938 |
| 4 | 1.296679 | 2.228837 | 1.000000000 | -0.034281200 | -2.110352 |
| 5 | 1.886951 | 2.231934 | 0.989361702 | -0.003873250 | 0.027853 |
| 6 | 1.850226 | 2.295278 | 1.000000000 | 0.114366650 | 0.406544 |

Every candidate arm: 31 captures, zero dropped slots, zero capture exceptions; total 186 captures. Peak raw ring: 11 frames = 3,379,200 bytes, below the inherited 12-frame limit. Median callback-count ratio 1.0 is within [0.97,1.03]; median p95-gap increase 0.0220914 ms is below 2 ms; worst matched max-gap excess 0.406544 ms is below 10 ms. Every capture p95 is below 10 ms and runner CPU below 20%. Severe baseline stalls: 0. All inherited cost gates pass. All twelve fixture/Xvfb children were reaped and private sockets removed.

## Audit and provenance

Predecessor runner/fixture/auditor Git hashes verified 3/3. Fixture and full measured code region remain byte-identical. Two added runner lines export evidence only AFTER measured stop and fixture exit. The separate supervisor supplies fresh displays 17100..17111, task/output identities and per-arm persistence.

Frozen independent audit: PASS, integrity errors [], cost failures [], twelve arms checked, 62 terminal-ring payloads independently hash/identity/age verified. Five copied-result corruptions rejected 5/5. Exact predecessor auditor also returns PASS_X11_TEMPORAL_CAPTURE_OVERHEAD_SCOPED with errors []. All 17 frozen source/plan/control members remain unchanged postformal.

Source freeze HEAD: `9e9de04a760bede62e40928240bf4765e33f366b`.
Source archive SHA-256: `72f75186ea7d08f5a607d3a7e2937a6547adb0f0384803f0dbb73be7a940f270`.
FORMAL_RESULT SHA-256: `8e50dbc870ba29af199214337ef452d683482feadfe1e037e43f387aea2f9e8a`.
INDEPENDENT_AUDIT SHA-256: `880331383e65eff879057165bb8ecc3dfb6381ba298ce6176ada8c13743244f4`.
CORRUPTION SHA-256: `6f930b4e8c02fb31fdf227ceed3e6d845f99101f9c4591ae6ef3b9124288bf18`.

## Interpretation and retained limitations

This does not support a fixed 15-20 Hz performance ceiling. It does not prove that scheduler noise caused #1061's historical rejection; environmental nonstationarity remains an alternative, not an identified cause. Separate historical blocks are not concurrent randomized cadence arms on a verified identical physical host.

The following were disclosed before formal: CPU measures only the runner, excluding Tk/Xvfb; original end-window overshoot and terminal Tk callback are preserved; absolute capture stamps outside the terminal ring are NOT_RECORDED; terminal begin times are exact end-minus-duration derivations; peak-ring memory remains a producer scalar. Terminal payloads, ages and read-only query membership are independently checked. All returned frames remain historical and grant no input authority. Post-window export is outside measured intervals but may affect between-arm workload.

Interactive transport was rejected before any process or invocation marker existed. After verifying that absence, ordinary noninteractive container execution launched the same frozen supervisor exactly once. A package-metadata lookup failure also occurred before construction; dependencies were not changed.

Git retains the recoverable frozen source and exact aggregate result/audits. Full raw callback/timing/cleanup evidence and synthetic terminal-ring pixels are retained in the conversation evidence archive, not claimed as Git-retained. No model-demand, task correctness, token, real-desktop privacy, high-DPI/compositor, total-host CPU or hard-real-time claim follows.

Stop this allocation. The next question should be temporal-evidence adequacy or a separately designed variance/endpoint comparison, not finer threshold bisection inferred from these non-pooled runs.
