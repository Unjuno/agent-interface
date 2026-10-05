# Result: A02 source attribution

**Disposition: `PASS_ATTRIBUTION_ONLY`.** Frozen-source candidate A05 passed 12/12 assertions; independent raw/source auditor v2 passed with zero errors. The read-only trace contains two key-up edges and two `keymap-sample` events between them. Source attribution shows these samples are the historical V12 fixture owner's per-key physical probes: the first explicit up's post-sample and the next explicit up's pre-sample. The A02 adapter joins the measurements, while its fixture loads the historical owner under `map01_attack_onset_phase_allocation_02_v1/dependencies/v12/`.

The current V39 V15 source closure selects `doom_owner_thread_release_batch_backend_v1`, `input_transition_owner_v4` → `input_transition_owner_v3` → `live_control/input_owner_v12.py`. Its explicit up path sends `KeyRelease` and `XSync`; neither transition wrapper performs an inter-release keymap query. The current owner's sole `query_keymap` call is inside terminal `release()` cleanup, and the ordinary backend release batch takes one owner-state sample after explicit key-ups. Thus A02 does not show a production release-order conflict.

This audit also narrows the next technical gap: current V39 does not have A02's per-key physical key-state measurement. Its XSync receipt records server synchronization and does not establish application consumption. This package executes no live X11, GUI, OS input, game, model, task-effect, threat-response, recovery, or latency experiment; it does not close Issue #59.

## Preserved construction history

- `source-audit-a01/`: initial 11-condition source/trace audit; candidate and independent audit passed.
- `source-audit-a02/`: stronger probe-order condition selected a down-edge post-sample and returned `FAIL_SOURCE_ATTRIBUTION`; raw retained, no auditor invoked.
- `source-audit-a03/` and `source-audit-a04/`: corrected construction revisions passed; A04 explicitly checked the harness's historical dependency path.
- `source-audit-a05/candidate.json`: strongest candidate; 12/12 assertions pass.
- `source-audit-a05/audit.json`: first independent auditor failed because it compared AST nodes from separate parses; preserved unchanged.
- `source-audit-a05/audit-v2.json`: corrected independent raw/source audit passes with zero errors. Candidate and retained A02 trace were not rerun or modified.
- `preflight-source-audit-01.json` through `preflight-source-audit-03.json`: retained source-availability and candidate-script stops before analysis.

## Provenance

- Base: `69dd261430cb1ed875f5a76411c4a2a54777c114`
- Candidate run: `MAP01-V39-PERKEY-SOURCE-ATTRIBUTION-A05-20261005`
- Candidate source hashes: `results/source-audit-a05/candidate.json`
- Independent audit: `results/source-audit-a05/audit-v2.json`
- Whole-package file hashes: `SHA256SUMS`

To rerun the one-shot A05 candidate and raw/source auditor in a fresh worktree, use the commands in `README.md`. The tracked result path intentionally prevents replacing an existing outcome.
