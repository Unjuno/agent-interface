# Action-bound visual residuals — T0 result

## Disposition

The formal WSLc candidate ran once and exited 0 with `PASS_CANDIDATE_SHAPE`. A separate network-disabled WSLc auditor ran once and returned `METHOD_PASS_SCOPED` with zero errors. The result satisfies only the preregistered synthetic method gate; the start-gate SHA metadata discrepancy is retained in `FREEZE_CORRECTION.md`.

## Findings

All five scheduled events were detected by raw delta, global registration, and action-bound residual by their frozen deadlines; the mandatory critical cue was preserved. Across the two clean valid-pan non-events, the action-bound method made 0 false alarms versus 2 for raw delta. On the matched primary slice, both methods detected all 3/3 events with 0/2 versus 2/2 false alarms. Across the full 16-pair denominator, raw delta made 10/11 non-event alarms and action-bound residual made 8/11; the action-agnostic registration made 3/11 and also suppressed the observed no-receipt external scroll, which is why a small false-alarm rate alone does not establish valid causal attribution. The sham foreign-intent receipt fell back to full-frame observation.

Late or failed delivery, missing receipt, stale viewport, and stale focus each forced `UNKNOWN_FULL_FRAME`. Under/over-delivered actions and nonrigid/parallax changes remained visible as residual alarms. The unchanged no-input pair produced no alarm. Five of five independent corruption controls were rejected during construction validation.

These are counts on an authored finite fixture. They do not estimate natural event prevalence, real-world false-alarm or miss rates, efficiency, safety, application delivery, GUI correctness, or game control.

## H / T / D / C / U

- **H:** A source-bound conservative residual can keep exogenous cue detection at the raw-delta level while lowering false alarms during valid self-motion.
- **T:** Sixteen synthetic 16×12 raster pairs, five scheduled events, four methods, one formal WSLc candidate, one separate WSLc raw-only audit, zero formal retries.
- **D:** The independent auditor reconstructed all 16 rows and every method’s transform, residual, cue and fallback fields; 5/5 events met deadlines; primary recall matched at 3/3 while action-bound false alarms fell from 2/2 to 0/2; full-denominator rates and all fallback rows are retained in `SUPPLEMENTAL_SUMMARY.json`.
- **C:** Authored grayscale translations and event marks, stipulated receipt accuracy, fixed cadence and deterministic pixel patterns. Global registration had fewer total false alarms in this fixture but suppresses motion without proving it was self-induced.
- **U:** No model, GPU, GUI, live game, physical/synthetic input injection, real application event, safety, natural event rate, task usefulness, model-boundary saving, human-tempo or production claim. Memory enforcement was unavailable in the WSLc kernel.
