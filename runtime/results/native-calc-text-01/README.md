# Calc text conditions and explicit pacing integration

The previous Calc transfer visibly entered 16 when its native text payload was
116. This bounded probe varies edit mode (direct typing versus F2), payload
(116 versus 476) and explicit inter-character waits (0, 2, 10 ms). Two blocks
reverse condition and payload order, using 24 distinct cells in A1:C8. Cell
addresses contain no repeated digits. Setup, native guards and independent
saved-workbook reading reuse the existing Calc path.

The primary assistant grounds the name-box position once from the initial
image. The declared matrix then runs locally, minting and checking its exact
region per case; those 24 cases are automated controls, not 24 model decisions.
The assistant views the completed matrix and confirms Save/format visually.
Saved-file scoring is read only after all input decisions have ended.

## Actual result

| Inter-character gap | Exact saved cells | Total |
|---|---:|---:|
| 0 ms | 7 | 8 |
| 2 ms | 8 | 8 |
| 10 ms | 8 | 8 |

The sole mismatch was C8: second block, direct typing, 0 ms, intended 116,
actual 16. Its matching first-block condition succeeded. Every F2 case and
every 476 case succeeded. This reproduces intermittent loss in the declared
conditions; two observations per condition do not establish cause, minimum
safe pacing, general reliability or a performance benefit.

The research Calc harness now accepts `--text-gap-ms 0|2|10` (default remains 0).
The explicit policy expands literal text into ordinary text/wait operations;
the existing complete-program preflight, admission, operation limits and
release checks still apply. It adds no keyboard-layout support or authority.
Recorded native programs contain every added wait. The shared helper's payload
expansion was checked against all 24 actual matrix programs; they match exactly.

In `self-use`, the assistant repeated the original 116/476 task with the same
entry request and 2 ms policy. Both values appeared correctly before Save and
were independently verified in the retained workbook. It needed two input
programs (entry/Save, format confirmation), with no value-repair program.
This is one fresh successful task, not a randomized matched comparison.
Post-dialog BadWindow feedback still requires review; that gap is unchanged.

## Retained attempts

* `probe-1`: explicitly interrupted before grounding/input when the initial
  allocation was found to contain repeated digits in A11/A22 addresses. Blank
  workbook, original source, reason and cleanup remain retained.
* `probe-2`: invalid hyphen in a private alias rejected minting before dispatch.
  Failed source and traceback retained; the alias was corrected to underscore.
* `probe-3`: first case completed, then the changing name-box text caused an
  exact-pixel refusal before the second case. No replay and no saved matrix score.
* `probe-4`: same corrected code, with the assistant choosing a fixed name-box
  boundary at [119,108] instead of the changing text at [18,108]. All 24 input
  programs completed; independent scoring found the one mismatch above.
* `self-use`: 2 ms integration into the original two-cell task, final [116,476].

The native backend and core were not changed. The matrix's executed source is
retained under probe-4; final-source factors identical payload expansion into
the Calc harness helper. Earlier failed sources are retained where different.
Unchanged dependencies come from base commit
`0d79068cd129df93becc702337de5af58d45175d` and the prior native Calc/feedback records.
There are 155 verified native image/hash links and 456 manifest files;
SHA256.json excludes itself and this README. Original artifact paths remain in
JSON; unchanged PNGs are copied beneath each bridge's images directory.
All tracked subprocesses have terminal return codes, not universally zero exits.
No helper model was used; primary model tokens/cost remain unknown.

## Method references and reproduction

The [official Calc 24.2 guide](https://books.libreoffice.org/en/CG24/CG2402-EnteringandEditingData.html)
distinguishes direct replacement from F2 editing. The
[XTEST protocol](https://xorg.freedesktop.org/archive/X11R7.7/doc/xextproto/xtest.html)
defines CurrentTime as no requested event delay. These informed the conditions;
neither source explains the observed loss. This probe uses ordinary local wait
operations, not XTEST's server-side delay field.

```
PYTHONPATH=. python3 research/live_control/probe_native_calc_text_v1.py --out results-local/my-calc-text-matrix
PYTHONPATH=. python3 research/live_control/run_native_calc_self_use_v1.py --out results-local/my-paced-calc --text-gap-ms 2
```

Both request explicit primary-assistant grounding files from fresh images.
Do not reuse coordinates without inspecting the current scene. Keep this
policy opt-in until further held-out evidence supports a default change.
