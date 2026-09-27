# Repeated input-state values: lossless companion table

`input_state_table_v1.py` factors common values from the before/after input-state
samples of exchange observations. This addresses the long repeated state dumps
manually reviewed during GUI field repair without changing runtime observations,
image capture, input admission, or the existing receipt's attention list.

The existing lossy presentation mode can omit transient visuals during settle;
see PRESENTATION.md. It was not enabled for this work. This candidate selects only
four named fields (`input_state_before`, `input_state_after`, `input_state_scope`,
`owner_revision_unchanged`) and preserves their JSON values exactly. Every other
observation field, image, feedback, terminal and exception remains in the original
report/receipt; the companion must be read alongside that evidence.

## Representation

`common_state` contains state keys with the same value in every dictionary sample.
Each sample retains its differences. `common_observation` similarly factors shared
metadata. Every observation keeps its source path and sequence; duplicate sequences
are not discarded. Missing fields remain missing, null remains null, and literal
non-dictionary states are retained rather than normalized. Unknown nested fields
remain intact. Comparison distinguishes booleans, integers and floating-point
values. Nonfinite values are rejected instead of silently serialized as JSON.

The builder reconstructs the selected rows and compares canonical JSON values
before returning. This is lossless at the parsed JSON-value level, not original
source-byte formatting, JSON duplicate-key retention, or schema/authenticity proof.
The original report's byte hash is included. No attention is cleared, no sampled
state becomes current authority, and a round trip does not imply valid input state.

## Fixed-trace results

Sizes below use the same compact UTF-8 JSON serialization. The full companion
includes source hash, scope and authority text; it is the realistic output overhead.

| Existing trace | Observations | Original selected rows | Table alone | Full companion |
|---|---:|---:|---:|---:|
| GUI repair save | 4 | 3558 | 1505 | 1884 |
| GUI repair field edit | 8 | 7142 | 2784 | 3163 |
| GUI repair resave | 4 | 3570 | 1510 | 1889 |
| Post-correction tracking loss | 3 | 2682 | 1644 | 2023 |
| False local visual goal | 2 | 1797 | 1165 | 1544 |
| Interrupted key hold, no observations | 0 | 2 | 61 | 440 |

The zero-observation case gets larger: the wrapper is overhead, not useful state
compression. Do not append an empty companion in a live caller. Total report or
model input is not measured by these selected-field figures. The assistant read
the field-edit table in this turn, seeing common released input/focus/owner values
and per-observation revisions/times. That is offline review of familiar data, not
a new live recovery trial or matched usability measurement.

`probe_input_state_table_v1.py` checks six preserved reports and eleven synthetic
preservation controls: unknown nested exception/negative values, missing key, null,
bool-versus-int, int-versus-float, held button, changed owner, changed focus,
cancellation, empty rows and duplicate sequence. All round trips pass. These
controls test that adverse evidence survives encoding, not that a classifier
recognizes every fault or that the source itself is trustworthy.

## Reproduction and next validation

```sh
python3 research/live_control/input_state_table_v1.py research/live_control/results/gui-effect-live-01/recover/report.json
```

The probe writes an exclusive `results/input-state-table-01` directory; its report
pins source hashes and source-report hashes, and the recovery table is preserved.
Original frozen files are unchanged. No token accounting, speed comparison,
runtime promotion or Research Freeze follows.

Next integrate this as an optional **replacement for the extra raw state dump**,
not an additional duplicate presentation. Keep the full receipt and final image,
do not emit empty companions, and compare a fresh field-edit task with changed
values/layout. Test if the model can still inspect interruptions and changed state
without full-state expansion. Separately investigate capture count: this companion
alone saves no captures, socket calls or waiting time.
