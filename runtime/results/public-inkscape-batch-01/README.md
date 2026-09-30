# Public pointer batch — primary Inkscape use

The primary assistant used the public portable relay and exported Node host built
from `73d3475dd478766e5d35da929a5f340244f5b3a6`, outside the checkout under
Python `-I`. A fresh private WSL Xvfb/Openbox session opened Inkscape 1.2.2 with
an empty 400x240 SVG. No provider subagent, sensor, action queue or automatic
repair was used. This is an integration use record, not a frozen comparative
performance experiment.

The task was to create two distinct rectangles inside the page and save the SVG.
The assistant reviewed the initial exact reply image, selected page coordinates,
then dispatched one 15-operation program: focus, select rectangle tool, two
pointer drags, explicit fixed waits, observe and release. The returned image
showed both rectangles inside the page. A separate 5-operation save program
returned the same shapes and no unsaved title marker. Three exact reply images
were delivered to the primary assistant and attributed with explicit attempt
reviews. No correction or replay was needed.

Independent saved SVG inspection found exactly two positive, non-overlapping
rectangles wholly inside the page. Their widths/heights are 132.20338/71.18644;
origins are (32.542374,36.610168) and (215.59322,128.13559). This proves the scoped
saved-file task predicate, not arbitrary precision dragging or generic GUI
correctness. The source/binding assertions and 120-second lease were supplied
by the caller from the prior capture clock; no server freshness authority is
inferred. Fixed waits are not redraw acknowledgments.

Five relay calls: observe, draw dispatch, save dispatch, read-only full-result
lookup and close. The draw/save requests opted into partial success summaries;
full-result lookup returned the same raw source digest without an image or new
input. Both dispatches and close recorded verified release. Transport exited 0.
All owned setup/application processes are terminal; application termination was
caller cleanup after save (Inkscape -15, Openbox 1, Xvfb 0), not a claim that all
application exit codes were 0.

Host send-to-retained-reply intervals in milliseconds were approximately 1693.37
(initial startup/observe), 325.32 (draw), 177.12 (save), 26.78 (lookup) and 44.85
(close). These are transport intervals, not model reasoning, first useful
feedback, semantic completion, human tempo or comparative speed. There is no
unbatched baseline, token count, cost measurement or wait-default proposal.

The public tool description and host guide now explain the exercised drag
sequence and splitting at a visual decision boundary. Execution semantics are
unchanged. The original research and prior allocations are unchanged.

`raw.tar.gz` retains build/host manifests, exact requests/replies, images,
programs, primary review receipts, host events, SVG, task evaluation and cleanup.
`draw-program.json` uses coordinates selected from this capture; do not transplant
those coordinates or the lease into another allocation. The fixture's display
setup is host preparation, not primary GUI control. Related discovery and host
test logs are included. `python -O verify.py` checks bytes, saved task predicates,
review attribution and recorded outcomes; it does not prove perception, model
visibility timing, clock authority or a universally safe batch.
