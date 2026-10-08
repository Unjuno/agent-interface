# Existing pixel-quiet observation in the agent's actual loop

Seed 991075, private Linux/X11 Calc. No runtime or client source changes. The
assistant appended the existing `settle` step (quiet 200 ms, timeout 1200 ms) to
the input/save program, then viewed its returned image. It showed the complete
format dialog, allowing the next explicit decision without a separate observe
program. The second program pressed the observed focused Excel-format button
with Return, then settled again. Its returned image showed the dialog gone.
Independent evaluation and direct saved worksheet XML both confirm A1=766,
A2=761. Both terminals verified empty input release; server cleanup exited 0.

Settle reported pixel quiet after 5 samples / 283.422854 ms and 7 samples /
445.363011 ms. These are runtime measurements, not hard timeout guarantees.
The assistant viewed sequences 1, 11 and 19. Native capture sequences reached
19; extra local observations are a real cost, even when the model sees only
the newest one. Reused exact images are explicitly referenced, not guessed by
sequence number.

There were two programs and six socket exchanges before cleanup (initial read,
two clocks, two submits and final drain). The earlier seed 991074 required a
separate observe program. This is a structural self-use result, not a controlled
speed comparison: seed, scheduling and conversation differ. In this run the
report-to-next-call gap remained 18,559.617567 ms, and first program start to
final report was 20,760.472711 ms, excluding setup and cleanup. Human-tempo
operation remains unproved. No model token counts are available.

Use pixel quiet only as a presentation hint. Static blank frames may still be
incomplete; moving interfaces may time out. Input authority does not renew, and
task success still comes from independent evidence. Preserve this as an opt-in
recipe, not a new default wait for all actions.

Evidence: `runtime/` contains original events, AIT/PNG frames, source manifest
and saved workbook; `enter/` and `save/` contain exact requests, preparation,
replies and reports. `client-source/` copies the unchanged client and settling
components. `SUMMARY.json` records measured scope and raw-derived values;
`SHA256.json` covers evidence before this README. Historical paths are unchanged.
