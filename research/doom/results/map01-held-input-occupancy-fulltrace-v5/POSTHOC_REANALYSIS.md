# v5 retained-trace reanalysis record

## Scope and decision

This is deterministic posthoc reconstruction for the completed-hold early-release boundary repair. It is not a new live GUI/game experiment, does not rerun the original allocations, and does not modify any frozen raw input or v4 output.

**H:** a completed hold's interval must end no later than the earliest verified empty-input release that precedes the final post-release snapshot.

**T:** execute candidate v5 once on the retained v38 and v39 report/event pairs, then execute the separately implemented raw auditor v6 once over both outputs. Compare every hold row, decision intersection, and total against frozen v4 outputs.

**D:** PASS if v6 reports both runs as raw reconstruction PASS with zero errors, source hashes match, and v5 rows/intersections/totals exactly equal v4. FAIL on any unaccounted hold, mismatch, hash drift, or negative/impossible interval.

**C:** the correction is restricted to completed holds with an earlier verified empty-input release. Rows without that event preserve prior behavior. This test cannot establish physical occupancy beyond the timestamps retained in the event stream.

**U:** retained events do not expose exact ordinary key-up time. Equality on v38/v39 means the reported historical measurements remain unchanged; it does not prove broader runtime behavior or task effectiveness.

## Frozen inputs and provenance

Raw inputs were fetched from repository main commit 4ca1db66b6adcb4ea15fc3c744315ad39a87749e, corresponding to full-trace v4's already-retained source data:

| File | SHA-256 |
|---|---|
| v38 report.json | 7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58 |
| v38 runtime/events.jsonl | 80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3 |
| v39 report.json | 719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687 |
| v39 runtime/events.jsonl | 2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381 |
| frozen v4 v38.json | 2aeec615483a754233c5b9d483be001952e7ca6cd66370bd1e90bf0389427eee |
| frozen v4 v39.json | 1cd61f82a2ff832131be4a448bc90663f01c4acaab278807a969d2ef24a3b889 |

All four source hashes match the existing v4 freeze. The analyzer and auditor wrote only new v5 output files.

## Executed commands and outcome

Environment: Windows host, Python 3.11.9; deterministic CPU-only posthoc reconstruction. No model, GUI, game process, or input was used.

From the task workspace, using a dedicated temporary input tree downloaded from the pinned main commit and a separate fresh candidate output directory:

```powershell
python research/doom/analyze_map01_held_input_occupancy_fulltrace_v5.py outputs/occupancy-early-release/raw-repo/research/doom/results/map01-v38-integrated-threat-live-01 --out outputs/occupancy-early-release/candidate-v5/v38.json
python research/doom/analyze_map01_held_input_occupancy_fulltrace_v5.py outputs/occupancy-early-release/raw-repo/research/doom/results/map01-v39-coast-liveness-live-01 --out outputs/occupancy-early-release/candidate-v5/v39.json
python research/doom/audit_map01_held_input_occupancy_fulltrace_v6.py --repo outputs/occupancy-early-release/raw-repo --candidate-dir outputs/occupancy-early-release/candidate-v5 --out outputs/occupancy-early-release/audit-v6.json
python research/doom/test_map01_held_input_occupancy_fulltrace_v5.py
```

All commands exited 0; the construction/regression suite printed PASS 6 fulltrace-v5 tests. Auditor output map01-held-input-occupancy-fulltrace-v6-audit reports both runs raw_reconstruction: PASS, source_sha256_matches: true, and errors: [].

| Output | SHA-256 |
|---|---|
| v5 v38.json | a80b77fc0f48aa9fb0076106aa16b28e479f9400f0f2f4ac41f3f8c6e65e777f |
| v5 v39.json | fe0338ab39aaaf38c74181a78c9343264b70127589bb6666c4f31ca21538f7ab |
| v6 audit-v6.json | f5033e9b315ca62fe4f568ffc7b3f90398def4089beb4c07e3ccadad2b4354 |

**Decision: PASS, scoped to the immutable v38/v39 event streams.** Candidate v5's holds, decisions, and totals are exact JSON matches to each frozen v4 output. v38 remains 11 hold rows with model-wait total bounds 3,048.890–4,039.878 ms. v39 remains 29 rows with model-wait total bounds 6,301.200–8,452.733 ms, including one partial admission/cancel-ack race. No historical totals changed.

