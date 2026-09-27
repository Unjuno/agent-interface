# Result — calibrated clock conversion at RunningActionGuard (#4544)

**Amended disposition:** clock-calibration arithmetic PASS; the original guard execution is not independently evidenced because its exact inputs and receipts were not retained. The corresponding guard outcome is now supported by a separately identified deterministic replay below—not by recovered original receipts.

## Execution

One persistent container used image `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e` (linux/arm64), started with `--pull=never --network none --read-only` and a 16 MiB no-exec tmpfs. The container ran only a sleeping Python process and monotonic-clock queries. The exact main sources were loaded into that same image for the guard evaluation; no source was mounted writable.

Three same-session brackets yielded host-minus-container intervals:

| Probe | Host before | Container capture | Host after | Offset interval |
|---:|---:|---:|---:|---:|
| 1 | 15598434459250 | 14859470998659 | 15598667112375 | [738963460591, 739196113716] |
| 2 | 15598769735791 | 14859794740452 | 15599113997750 | [738974995339, 739319257298] |
| 3 | 15599194169125 | 14860213238731 | 15599414455083 | [738980930394, 739201216352] |

Intersection: [738980930394, 739196113716] ns; width 215183322 ns. The conservative capture translation used the intersection's lower bound: third container capture + 738980930394 = 15599194169125 host-domain ns. Host controller decision was 15599509469625 ns.

| Case | Apparent age | Validator | Guard state | Authority |
|---|---:|---|---|---|
| Raw container capture vs host decision | 739296230894 ns | REJECTED_STALE | CANCEL_REQUIRED | false |
| Conservatively translated capture | 315300500 ns | VALID_CURRENT | INPUT_ACTIVE | true |
| Translated capture shifted 31 s older | 31315300500 ns | REJECTED_STALE | CANCEL_REQUIRED | false |

`result.json` retains the clock brackets and derived summary rows, but not the original guard inputs or full receipts. The original report's claim that it contains them was incorrect. Translation was arithmetic over the intersection of the three measured bracket intervals. The guard summary in that file was not independently supported by retained invocation operands at the time. No physical Executor program was submitted.

## Independent audit

`audit.py` recomputes each bracket, the common interval, width, translation, ages, threshold comparisons, and required dispositions. It also rejects four corrupted-result controls. It was run in the pinned container after reading back the committed artifact files.

## Deterministic replay and correction

The additive `replayed_guard_inputs_receipts.json` contains explicit deterministic fixture inputs and complete receipts produced by re-executing both production modules. It is classified `DETERMINISTIC_REPLAY_ONLY`: it does not recover what the original invocation consumed, and the synthetic accepted-program fixture is not an Executor event. The guard receipt consequently reports `physical_input_may_be_down=true`; this is a state-machine implication of that fixture, not evidence that any physical input was sent or held.

Replay used the same three clock brackets already retained above, the pinned `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e` image (linux/arm64), network disabled, read-only root, and a 16 MiB no-exec tmpfs. The Python harness and exact source bytes were staged only inside the container's ephemeral tmpfs. The replay builder, independent receipt auditor, and five corruption mutations all ran there. Result: `PASS_FULL_RECEIPT_REPLAY`; all five mutated-input/receipt controls were rejected. No new clock probe, model call, WAD/game, GUI, Executor process/input, formal allocation, cancellation, or physical release event was involved.

The replay verifies the complete receipts against the exact recorded source commit `91b5143989403754b360738c445f72b68b673718`. Both source files fetched at that commit matched their recorded Git blob IDs and SHA-256 digests. The main-branch commit later used while drafting the first replay scripts was different; those scripts were corrected to pin the recorded commit before the final replay.

The original v1 `result.json` is unchanged. This replay supports the reported guard-state transition for the explicit reconstructed fixture, but does not establish that the original invocation used those operands or that seed 990641 behaved the same way.

## Provenance and scope limits

Main source commit: `91b5143989403754b360738c445f72b68b673718`.

- `action_validity_admission_v1.py`: blob `31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e`, SHA-256 `f102cbde4f0e46c9f8e974e9f0a7d1c47f3fc662d7c8ba32699d16799d3db98a`.
- `running_action_guard_v1.py`: blob `d54047e78bc76f53ef47c6f70fd4a3be6318f09c`, SHA-256 `2d5feb69efd59fdca22e0db9e561923411490eb758eab9e2b8379714e20e5c62`.

This is construction evidence for one process-clock pairing and guard fixture only. It complements, but does not broaden, the opposite-sign offset and final-admission experiment already on main. The separate seed-990641 freshness exception remains unexplained because its exact capture/controller operands were not durably logged. No new formal allocation, gameplay, release, or runtime-success claim is made.