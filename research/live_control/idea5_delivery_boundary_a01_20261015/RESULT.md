# Idea #5 — actual CLI state/event delivery boundary

Disposition: **SCOPED_COMPOSITION_CHARACTERIZATION**, 2026-10-15. This turns one item from the organized idea agenda into executed evidence. Issue #5 remains open.

## Hypothesis, test, and decision

H: the existing state/event projection can preserve explicitly emitted critical events through its CLI archive/selection/output path; a selected-output log alone does not prove successful stdout delivery.

T: snapshot main `cb638a494b5ff88bf4852df08658abd10003a6c5`, then run the actual `interactive_v10.main()` and `interactive_v15.main()` with the actual Presentation/DeliveryLedger implementations. Replace only app Session/Backend and Executor boundaries with controlled no-input stubs. Cross two CLI versions, full/compact selection and healthy/broken stdout: eight cases per interpreter mode. Each source trace has a same-focus transient warning observation, an explicit critical signal, a later normal observation and a negative terminal. A pre-write BrokenPipeError tests zero accepted bytes, not partial delivery or a failed flush after accepted writes.

D: retain every synthetic source event in raw; preserve the explicit critical signal in selected output; distinguish selected records from captured stdout; accept v15 flush receipts only after successful output; never claim task success or model receipt. Characterize whether the visual-only warning survives, without claiming to detect pixels.

## Results

| Path | Raw | Selected full / compact | Healthy captured stdout | Broken captured stdout | Successful flush receipts |
|---|---|---|---|---|---|
| v10 | 10 | 10 / 8 | Equals selected | 0 | None in either case |
| v15 | 10 | 10 / 8 | Equals selected | 0 | Equals selected when healthy, none when broken |

The explicit `critical_signal` is preserved by both projections. The same-focus warning observation is present in raw but absent from compact output. The warning is represented by a synthetic observation/image-reference label, not a rendered image or a real application warning. This proves the metadata-based selection boundary only. Neither CLI has gained semantic warning detection.

Both clients continue after injected BrokenPipeError and retain `delivered.jsonl` despite zero captured stdout records. Therefore that filename denotes selection, not delivery success. v15's existing ledger supplies a useful additional local flush boundary: no successful flush receipt is written for these failed sends. Its successful local flush still does not prove transport/model receipt. Do not transfer this result to all clients or the current public CLI/MCP path; these are two explicitly selected research entrypoints, and v15 is labeled unpromoted by its source.

Decision: reuse the existing projection and v15 ledger as scoped components rather than introducing a new event/receipt mechanism from the idea text. Keep critical-event detection/retention and model-visible delivery as separate open integration requirements. The next composed check must trace these mechanisms into the selected supported caller and its acknowledgement/decision boundary; visual warning omission remains a separate information-loss question for a matched task study. This does not yet justify adopting compact mode globally or closing #5.

## Evidence and reproduction

- `SOURCE_HASHES.json` binds 31 byte-exact main source files under `source/`. These snapshots preserve source identity, including manifest-only dependencies; only the clients, projection, lease and ledger modules execute as real components here. GUI/backend/Executor behavior is synthetic.
- `output/` preserves the first exploratory eight-case run. After adding explicit output-directory and script identity metadata, `output-normal/` and `output-optimized/` retain the final script's runs; earlier exploratory bytes are unchanged.
- Each case retains actual emitted raw, selected records, captured stdout, source manifests, synthetic input trace and owner log. Empty owner logs are stub artifacts, not physical release evidence.
- `SUMMARY.json` includes the probe digest, frozen-source manifest digest, Python version, optimization flag and explicit no-GUI/no-model scope.
- Independent `audit.py` imports neither the CLI nor projection; it checks raw event order, expected selection, output equality and flush identity/byte/timing consistency. Both final runs pass its eight-case audit. Auditor mutation checks reject a lost critical event, a fabricated successful flush on a broken stream, fake received rows, and a missing matrix case; the unchanged matrix is accepted.

From this directory, use **new** output directories for a construction rerun:

```text
python run_probe.py --out fresh-normal
python -O run_probe.py --out fresh-optimized
python audit.py fresh-normal
python -O audit.py fresh-optimized
python -m unittest -v test_audit
python -O -m unittest -v test_audit
```

One unittest method runs eight subcases per mode, rather than eight separately named test methods. Both final compositions pass; the auditor mutation suite has five tests. No WSLc allocation, GUI, X server, physical input, real Executor, model invocation, task effect, recovery, token or latency comparison occurred. The fixed synthetic terminal is `needs_decision`; independent evaluation explicitly records `success=false` and `synthetic=true`. No production/default changed.
