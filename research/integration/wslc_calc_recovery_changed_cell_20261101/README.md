# Calc recovery after a separate cell edit

This extends the fixed post-entry-yield recovery probe. After the compiled graph enters 731/864, yields on a context change and its owner closes, a separate test owner attempts to select A1 and enter 999. The recovery owner then has at most two seconds to observe the expected filled-cell reference; it is not permitted to replay entry or Save when that cue is unavailable. These are isolated, scripted WSLc tests, not an autonomous multi-user system.

| Allocation | Test actor | Recovery outcome | Persisted file | Final X input |
|---|---|---|---|---|
| n01 | Guard refused before dispatch because reviewed context pixels changed between observations. | Not reached | Blank | Neutral |
| n02 | After a bounded pre-observation gate, one guarded input completed and released; fresh screenshot OCR read A1 as 999. | All 16 fresh cues mismatched; no recovery mint, program or Save. | Blank | Neutral |

n01 is preserved as a failed setup attempt. The distinct n02 candidate adds bounded passive waiting for the old context and cell reference before the test actor acts; the input guard still rechecks context. Its first pre-observation was not ready and its second was. Both original compiled receipts remain SAFE_YIELD / effect_unavailable with one completed entry and verified release. In n02 the prior owner, test actor and recovery owner had distinct session IDs; the test actor and prior owner reported verified release. The final recovery owner did not dispatch input, so its close did not need an input release.

The n02 actor program explicitly requested 999 and the independently processed post-action screenshot produced Tesseract TSV text `999` at confidence 96.49. This is visual evidence of the changed display, not a direct internal-memory read; the intentionally unsaved file is independently parsed as blank. Both trials used two gpt-6.1-sol low calls. n01 recorded 25,779 input tokens (20,352 cached subset) and 140 output; n02 recorded 25,763 input (12,160 cached subset) and 124 output. Cached input is included in input. The host model calls were separate from private network-disabled Xvfb/Calc WSLc containers with 1 CPU / 1 GiB.

`public.zip` retains both frozen candidates, conditions, observations, model usage, action receipts, OCR inputs/outputs, saved bytes and cleanup. Run `audit.py` without Python optimization and with Pillow to check archive/source/candidate hashes, n01's changing context and refused input, n02's actor program and OCR crop, all recovery screenshot mismatches, absence of recovery input, blank FODS and neutral final X state. Private protocol journals and host path-bearing commands are omitted and not independently audited.

This uses a known fixed-value visual reference, one scripted edit and one fixed layout. It does not establish recognition of arbitrary edits, successful conflict resolution, mid-keystroke failure recovery, general reliability, MAP01 or project completion. Issue 57 remains open.
