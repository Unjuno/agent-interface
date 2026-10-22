# Terminal 4%-to-0% window — posthoc reconstruction

## H / T / D / C / U

- **H:** On the retained failed Astra attempt, the interval from decision 11's 4%-health source observation through its post-action sequence 504 sample contains the reported controller-model wait and a three-command response; health is manually transcribed as 0% at decision 12.
- **T:** Join report decisions 11–12 to exact event observations 459, 498, 501, and 504 by source-image basename and receipt sequence. Recompute intervals from raw monotonic timestamps, bind the selected frame hashes, and independently recompute all timing arithmetic.
- **D:** `PASS_POSTHOC_CLOCK_RECONSTRUCTION` means all required source-image/sequence/receipt joins and input hashes match. It is not a scientific success or causal diagnosis.
- **C:** Health could have reached zero during the model wait or during any of the three executed commands. An enemy visible in the terminal selected frame may have entered the field of view earlier; the selected 4%-health frame has no visible enemy. No intermediate PNG pixels are available to resolve those alternatives.
- **U:** This is a single-run retrospective boundary reconstruction. Health digits and visual descriptions are manual reads of selected frames; exact intermediate pixels, lethal-damage time/source, threat onset, input-key edges, and counterfactual response are unavailable.

## Result

The selected 4%-health source frame is sequence 459. The next retained sample linked to the response is sequence 504, where the existing report/manual transcription marks 0% and dead. Their capture timestamps are 12,158.151 ms apart. The controller's recorded model interval is 10,692.805 ms; the report's separate `model_ns` field is 10,613,874,802 ns. After model end, the three-command bundle (`backward`, `turn_left`, `turn_left`) was accepted 28.124 ms later, and sequence 504 was captured 1,054.068 ms after acceptance. Post-action observations at 498, 501, and 504 have exact event records, but their PNG bytes are missing.

Manual inspection of the hash-bound selected frames shows the player facing a close wall with 4% health at frame 11, and an enemy close in view with 0% health/death at frame 12. This narrows the retained failure to a 12.158-second observation-to-observation window spanning inference and the response, but does not say when health reached zero or attribute cause to inference, command choice, or a threat. It does not demonstrate what a local guard would have done.

## Reproduction and audit

From repository root:

```powershell
python research/doom/map01_astra_hud_pairs_a01_20261005/terminal_window_reconstruction.py
python research/doom/map01_astra_hud_pairs_a01_20261005/audit_terminal_window.py
python -m unittest discover -s research/doom/map01_astra_hud_pairs_a01_20261005 -p test_terminal_window.py -v
```

Inputs and selected PNGs are hash-pinned in `TERMINAL_WINDOW_INPUTS.json`. The independent auditor rebuilds timestamp deltas and sequence/receipt joins from `events.jsonl` and `report.json`; it does not independently validate manual health transcription or visual interpretation. All files are additive; the prior pairwise and stream results remain unchanged.
