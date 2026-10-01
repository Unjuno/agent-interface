# Browser direct final result does not trigger an extra drain

The assistant used prepared_exchange_v4 with --drain-final on the known prefilled
local browser fixture, seed 991029. It viewed initial and form images, selected
the draft text, replaced it with t991029 and submitted. Independent evaluation
returned directly, so drain_final reported attempted=false. No drain request or
reply file was created, and no extra socket read was performed by that option.

Saved request contents match the goal. Audit verifies thirteen exact AIT/PNG
frames, both input releases, preparation regeneration, request lineage and the
full 22-record received prefix. Three socket calls precede cleanup: clock/read,
navigation/terminal, and replacement/outcome. The process exited zero. No early
effect event, runtime rejection or status query occurred.

First capture to client processing end was 47.961 s; form socket return to
submission admission was 13.934 s. Local navigation/replacement programs took
889.287/381.281 ms. These timings do not establish improvement over prior runs:
this is one familiar sequential fixture episode, and processing end is not model
receipt. Actual tokens and human reference remain unmeasured.

Together with Calc's ready-final actual use and gated-evaluation integration,
this shows the optional drain is conditional on early evidence rather than an
unconditional app-independent extra read. It is not coverage of arbitrary
desktop applications or the orthogonal game benchmark matrix. Known browser
draft replacement is not unanticipated recovery.

Evidence: results/drain-browser-self-use-01 and
results/drain-browser-self-use-audit.json, including runtime/client/fixture hashes.
