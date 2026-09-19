# Live Calc use of composed action and review

The assistant started one private Linux/X11 Calc session (seed 991073), viewed
the blank workbook, then used `agent_exchange.py --review` for each program:

1. Enter 772 in A1, 709 in A2 and press Ctrl+S. The combined response showed
   cells and completed input, but the capture preceded the format dialog becoming
   visible. Focus changed around publication; task completion was not inferred.
2. Explicitly request an observation. The returned image showed the format
   dialog with the Excel-format button focused.
3. Press Return as the final program. Saved-cell evidence verified both values.
   The returned image still contained dialog pixels despite the later context
   and saved effect. A command-free continuation obtained independent success.

No image-read tool call or host path conversion was used at these boundaries.
The assistant chose the next program only after seeing the combined response.
All three programs completed with verified empty input release. Explicit finish
closed the socket server with exit code 0. `runtime/sheet.xlsx` matches the
SHA256 recorded by saved-effect evaluation; independent actual is `[772,709]`.

This is a real self-use integration example, not a matched performance study.
Caller program exchanges took 761.951, 159.916 and 155.402 ms. Report-to-next-call
gaps were 18,013.657 and 24,899.504 ms, including deliberation, request preparation
and host/tool overhead. First program start to final program report was
44,413.794 ms, excluding initial setup and the later evaluation read/cleanup.
These are caller clock differences, not model inference or human-baseline times.
The large outer gaps remain: reducing transport calls has not demonstrated
human-tempo operation. Model tokens were not available.

The live run identifies three next integration needs: observation when display
publication lags a focus transition, following result continuation without
reissuing input, and eliminating repeated caller assembly of batch/output paths.
Do not automatically dismiss a dialog based on context alone or equate a
historical displayed image with post-effect confirmation.

Evidence: `runtime/` contains untouched runtime frames, events, source hashes and
saved workbook; `enter/`, `dialog/`, `save/` contain all exchange artifacts;
top-level requests, initial/final/finish replies retain the outer flow.
`adapter-source/` captures the client files used. Historical absolute paths are
unchanged. `SUMMARY.json` derives timing from raw caller reports; `SHA256.json`
covers evidence files before this README. Eleven adapter/review tests passed
on Windows and WSL, including review failure retaining a single action attempt.
