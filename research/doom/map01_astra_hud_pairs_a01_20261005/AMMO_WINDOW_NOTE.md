# Ammo decrease across a non-fire plan — posthoc reconstruction

## H / T / D / C / U

- **H:** In this retained trace, a large ammo decrease between decisions 4 and 5 is bracketed by exact observations while decision 4's plan is non-firing and its recorded held-key summaries contain no `space`.
- **T:** Join decisions 3–5 to exact events at sequences 117, 148, and 211. Compare manual HUD ammo counts, planner/compiled actions, `keys_held` records, and available event types. Independently recompute the joins and deltas from `report.json` and `events.jsonl`.
- **D:** `PASS_POSTHOC_JOIN_HOLD_CAUSAL_ATTRIBUTION` means the source sequences, action rows, and recorded held keys join consistently. The scientific interpretation remains HOLD because telemetry cannot establish actual key-up or individual shot times.
- **C:** The manual HUD count could be wrong; source and intermediate capture pixels are absent; a prior firing key may have remained active or emitted shots during the following inference; event logging may omit releases. These alternatives are not distinguishable from this trace.
- **U:** Single failed run, manual ammo reads, no exact intermediate PNGs, no key-up/physical-state samples, no causal or counterfactual evidence.

## Result

Decision 3 starts at 50 ammo and contains `advance_fire`/`fire`; the next exact selected sample, sequence 148, is manually read as 48. Decision 4 starts at 48 and its plan contains only `backward` and `turn_right`; sequence 211 is manually read as 37, a further 11-ammo decrease over 13,090.934 ms. The corresponding `keys_held` summaries list only `Down` and `Right` for decision 4's plan. The raw event stream contains no explicit key-release event type. This is an action-to-ammo observability gap, not evidence that fire remained held or that the controller malfunctioned.

This result motivates retaining per-key release evidence and typed ammo samples in the next authorized live episode. It does not authorize or start one.

## Reproduction

```powershell
python research/doom/map01_astra_hud_pairs_a01_20261005/ammo_window_reconstruction.py
python research/doom/map01_astra_hud_pairs_a01_20261005/audit_ammo_window.py
python -m unittest discover -s research/doom/map01_astra_hud_pairs_a01_20261005 -p test_ammo_window.py -v
```

Input file hashes are pinned in `AMMO_WINDOW_INPUTS.json`. The independent audit re-joins raw report/event data; manual HUD transcription and physical key state remain unaudited.
