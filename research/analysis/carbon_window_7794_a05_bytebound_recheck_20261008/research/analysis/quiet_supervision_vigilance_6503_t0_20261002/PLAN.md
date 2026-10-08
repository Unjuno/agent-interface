# Issue #6503 T0 — finite vigilance-scoring method check

## H / T / D / C / U

- **H:** A small finite scorer can retain the full anomaly-opportunity denominator and distinguish hits, misses, false alarms, no-response, visibility, and hard machine stops without treating a late hit-rate decline as perceptual sensitivity loss.
- **T:** No-participant synthetic recorded-episode ledger; three four-opportunity blocks (early, middle, late) with independently sealed truth and visibility; continuous quiet, matched-count checkpoint, and hard-stop control displays. The formal rung tests only source/truth/display consistency and scoring arithmetic.
- **D:** `PASS_METHOD_SCOPED` only if all 12 assigned opportunities remain in their declared blocks; invisible events cannot become observable hits; no-response/miss/false-alarm counts reconstruct; checkpoint policy receives no hidden truth; mandatory machine stops are identical and unsuppressed; and dropped opportunity, oracle leak, visibility flip, and hard-stop suppression mutations are rejected. No human/vigilance result follows.
- **C:** This tests stimulus/scorer integrity only. It does not identify whether a person saw, discriminated, understood, or acted on a cue, nor separate perceptual sensitivity from response criterion.
- **U:** Hand-authored finite ledger; no rendered UI, participant, human behavior, time-on-task effect, power, prevalence, or runtime/product inference.

## Frozen fixture design

Four event classes are repeated in each of three position blocks: actionable visible anomaly, benign visible change, invisible/unavailable anomaly, and verified-success control. Each opportunity has a unique opaque token, source/effect state, visibility state, permissible safe action set, and independent scorer label. Display policy may expose only source-bound evidence available at its declared checkpoint; oracle truth remains auditor-only. A hard-stop event is a machine invariant rendered identically under every display arm.

This deliberately does **not** simulate a human response or claim that a checkpoint policy catches events between reviews. Nonresponse is a scored outcome category, not imputed as a perceptual miss or as safe.

## One-shot protocol

Before formal execution, run host construction tests, freeze all source digests, and commit the freeze receipt. Then invoke candidate once and a separate raw-only auditor once. No retry, source correction, or reclassification under this allocation. Preserve exact stdout/stderr, exit status, raw rows, audit, hashes, and limitations.

No model, GUI, participant, network, Docker/OrbStack, or external data. Host Python version/platform are recorded. This is a deterministic local CPU method rung.

## Preformal design disposition

The current construction implements only an opportunity/display ledger. It has no response-state fixture or independent hit/miss/false-alarm/no-response scoring function. Therefore it cannot pass the T0 scorer/material gate above. The 6/6 construction suite verifies only ledger construction and corruption rejection; it is not a formal allocation and no `FREEZE.json`, candidate raw result, or formal audit is claimed. Stop before allocation rather than redefining D after seeing the omission. A future successor would need a separately versioned response-scoring contract that does not masquerade scripted responses as human observations.
