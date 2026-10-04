# A02 isolated-position audit supplement

## H / T / D / C / U

- **H:** The retained A02 isolated-control `position` fields match the position encoded by each opaque token and the frozen design; a changed, otherwise-valid position is rejected.
- **T:** Read the committed A02 `isolated.jsonl` and A01 `design.json` without modifying them. Reconstruct all 16 token-bound expected positions. Run one positive check on the retained rows and negative controls for a different valid position and a missing position.
- **D:** Scoped PASS requires 16/16 retained positions to match and both negative controls to fail closed. Any mismatch or accepted mutation is FAIL.
- **C:** This checks only the isolated `position` field. It does not replace the original full auditor or independently re-audit all frame bytes, presentation rows, or provenance.
- **U:** No serial-interference model hypothesis, GUI effect, task outcome, runtime performance, or product claim is tested.

## Result

`PASS_POSITION_AUDIT_SUPPLEMENT`: all 16 retained A02 positions matched their token-derived expectations; the effective wrong-valid-position and missing-position controls were rejected. The original A01 auditor, A02 freeze, formal output, invocation counts, and historical PASS label were not edited or rerun. This supplement does not turn the field omitted by the original auditor into evidence that its original implementation checked that field.

The independent PR review identified that the original frozen auditor checked isolated frames and source indices but omitted `row["position"]`. This additive checker closes only that specific retained-raw coverage gap. It reads the A02 output in place and does not rewrite it.

The omission was reproduced without changing retained evidence: the committed frozen A01 candidate generated a temporary package; its 16 isolated rows equaled the retained A02 rows, and the unmodified package passed the frozen auditor. In a disposable copy, one valid `position` was changed and `SHA256SUMS` was recomputed. The frozen auditor still returned `ok: true`, while this supplemental checker rejected the same rows. This demonstrates a checker coverage defect, not corruption or invalidity of the retained A02 result.

An earlier attempt to use Git archive to materialize the 1,280 retained image blobs was stopped after lazy promisor-object fetching made no observable progress. A preceding attempt to use Windows-materialized files also failed because checkout CRLF conversion changed binary PPM representation; it was not treated as a scientific failure. The successful reproduction uses the frozen deterministic candidate and compares its isolated JSON rows against the retained rows before applying the disposable mutation; no retained output, freeze, or auditor was changed.

## Reproduction

From the repository root:

```text
python -B -m unittest discover -s research/analysis/serial_cue_interference_7387_t0_a02_position_audit_20261004 -p test_position_audit.py -v
python research/analysis/serial_cue_interference_7387_t0_a02_position_audit_20261004/audit_positions.py --design research/analysis/serial_cue_interference_7387_t0_20261004/design.json --isolated research/analysis/serial_cue_interference_7387_t0_20261004_a02/formal_01/output/isolated.jsonl
```

The regression test regenerates a disposable candidate package under the system temporary directory, checks its isolated rows against the retained A02 rows, and runs the original auditor on baseline and mutated disposable packages. Its mutation changes only `position` and refreshes the disposable checksum manifest.

No container, GUI, model, GPU, or OS-input invocation was made for this deterministic raw-field audit. The frozen A01 candidate was invoked locally only to generate disposable synthetic test data; no formal candidate result or retained output was regenerated.
