# Independent replay note — A01

From the repository root run:

```powershell
python research/doom/map01_astra_hud_pairs_a01_20261005/audit_pairwise_result.py
```

The auditor reloads the exact frozen report/frame inputs, rechecks their hashes, enumerates the raw 169-pair set, reruns the one-way guard for each pair, and checks pair status, pixel count, and no-authority/no-success fields against the retained JSONL. It imports the same guard under study by design; it independently recomputes the replay and does not independently validate the guard algorithm, manual HUD transcription, or any live behavior.
