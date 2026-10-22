# Analysis revision log

- **RUN01:** decoding and extraction completed; summary aggregation raised `KeyError: active_hold`. The first raw traceback and hashes for all 30 partial crops are retained in `ATTEMPT_01_FAILURE.txt` and `ATTEMPT_01.json`.
- **RUN02:** only the aggregation dictionary key was mapped from the emitted owner mode (`active_hold`, `coast`) to the report categories (`active_hold_inference`, `coast_inference`). Thresholds, source video, ROI, manual values and timing method remained the same. All RUN01 crop hashes match the retained RUN02 crop bytes.
- **AUDIT01:** the independent auditor initially failed its exact wording check although every data check passed. That raw failed audit is retained. README now states the required scope phrase; later audit runs are separately retained below.

- **AUDIT02:** the scope text check is case-sensitive; it again failed only on wording (`No live` vs `no live`) after all data checks passed. The README now contains the lowercase phrase.

- **AUDIT03:** a newly added preservation check ignored the `transition-crops/` subdirectory and raised `FileNotFoundError`; the stored original paths are retained and the auditor will resolve them relative to `ATTEMPT_01/`.

- **AUDIT04:** after resolving the crop-path issue and scope wording, the independent audit passed all source, video, transition, calibration, crop, decision-reference and model-window checks. See `AUDIT.json`.

- **Protocol wording:** post-run, the label-coverage control was narrowed to match the auditor (all prior values appear in the transcribed sequence; not every screenshot is time-aligned). This does not change pixels, thresholds, annotations, or model-window totals.
