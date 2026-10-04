# A02 manifest-integrity audit supplement

## H / T / D / C / U

- **H:** The retained A02 isolated-control `position` fields match the position encoded by each opaque token and frozen design, and the model-facing presentation manifest contains exactly 288 object rows with the documented fields. Changed/missing positions, answer-bearing extra fields, truncated manifests, and non-object entries must be rejected.
- **T:** Read committed A02 `isolated.jsonl`, `presentations.jsonl`, and A01 `design.json` without modifying them. Reconstruct all 16 token-bound expected positions; derive the expected presentation denominator from the frozen design; enforce object types and exact row-key sets; test wrong/missing positions, injected `answer`, truncated rows, and array entries. Separately reproduce each omission against a disposable candidate package with a refreshed checksum manifest.
- **D:** Scoped PASS requires all 16 retained positions and exactly 288 presentation object rows with expected keys, plus rejection of each effective negative control and nonzero CLI exit on rejected inputs. The frozen auditor's false accepts are recorded as coverage defects, not rewritten historical outcomes.
- **C:** This supplement checks isolated positions and presentation denominator/object/key schema only. It does not independently validate every presentation token, arm, source index, frame value, pixel, provenance claim, or other semantic property.
- **U:** No serial-interference model hypothesis, GUI effect, task outcome, runtime performance, or product claim is tested.

## Result

`PASS_MANIFEST_INTEGRITY_SUPPLEMENT`: all 16 retained A02 positions matched their token-derived expectations; all 288 presentation rows and 16 isolated rows matched the expected exact key sets. Wrong-valid-position, missing-position, injected-answer-field, truncated-row, and non-object controls were rejected, and rejected CLI inputs exited nonzero. The original A01 auditor, A02 freeze, formal output, invocation counts, and historical PASS label were not edited or rerun. This supplement does not turn fields omitted by the original auditor into evidence that its original implementation checked them.

The independent PR review identified two omissions in the original frozen auditor: the isolated loop checked frames and source indices but omitted `row["position"]`, and presentation rows were not restricted to an exact key set. This additive checker independently audits those two retained-raw coverage gaps. It reads the A02 output in place and does not rewrite it.

Both omissions were reproduced without changing retained evidence: the committed frozen A01 candidate generated temporary packages whose isolated and presentation rows equaled the retained A02 rows; the unmodified package passed the frozen auditor. In disposable copies, (1) one valid `position` was changed, and (2) an `answer: red_square` field was injected into a model-facing presentation row. After recomputing each disposable `SHA256SUMS`, the frozen auditor still returned `ok: true` for each mutation, while this supplemental checker rejected them. These demonstrate checker coverage defects, not corruption or invalidity of the retained A02 result.

An earlier attempt to use Git archive to materialize the 1,280 retained image blobs was stopped after lazy promisor-object fetching made no observable progress. A preceding attempt to use Windows-materialized files also failed because checkout CRLF conversion changed binary PPM representation; it was not treated as a scientific failure. The successful reproduction uses the frozen deterministic candidate and compares its isolated JSON rows against the retained rows before applying the disposable mutation; no retained output, freeze, or auditor was changed.

## Reproduction

From the repository root:

```text
python -B -m unittest discover -s research/analysis/serial_cue_interference_7387_t0_a02_position_audit_20261004 -p test_position_audit.py -v
python research/analysis/serial_cue_interference_7387_t0_a02_position_audit_20261004/audit_positions.py --design research/analysis/serial_cue_interference_7387_t0_20261004/design.json --isolated research/analysis/serial_cue_interference_7387_t0_20261004_a02/formal_01/output/isolated.jsonl --presentations research/analysis/serial_cue_interference_7387_t0_20261004_a02/formal_01/output/presentations.jsonl
```

The regression tests regenerate disposable candidate packages under the system temporary directory, check isolated and presentation rows against the retained A02 rows, and run the original auditor on baseline and mutated disposable packages. Mutations change only the target row field(s) and refresh the disposable checksum manifest.

The command-line contract is also tested in child processes: a corrupted position and a truncated presentation manifest must each produce JSON `ok: false` and exit status 1, so scripts cannot mistake an audit rejection for success.

No container, GUI, model, GPU, or OS-input invocation was made for this deterministic raw-field audit. The frozen A01 candidate was invoked locally only to generate disposable synthetic test data; no formal candidate result or retained output was regenerated.
