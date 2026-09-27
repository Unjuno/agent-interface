# Image after explicit target selection

Implementation source: `f715988a9d677f4b4b4f83a3fdf8ebfab7761d79`.
One new primary-agent Inkscape session (seed 991308) used public persistent MCP
in private WSL/Xvfb. No helper model, sensor, automatic repair or input replay.

The primary reviewed the image returned by explicit target selection (action 3,
binding revision 2, metadata matched), then selected the entire filename
(action 4), reviewed the selection, entered `saved-copy.svg` (action 5), reviewed
its exact value, and clicked Save (action 6). That frame still showed the dialog,
so the primary requested a fresh observation (action 7), without repeating Save.
The final image showed the requested title and x56/y50/w40/h30. Independent SVG
parsing confirms those values and the unchanged original x50/y50/w40/h30.
Explicit close verified empty keys/buttons; the runner exited 0 and fixture
cleanup returned. The exit code was observed in the conversation; the retained
cleanup/evaluation receipts independently cover their narrower claims.

Nine public calls, four input dispatches, eight images. The previous separate
post-review observation trial used ten calls, but this new single trial is not
a controlled latency comparison. Only one explicit call composition is shown.
Actual model tokens/cost, broad reliability and human-tempo operation remain
unmeasured. Matching metadata does not acknowledge redraw or semantic completion.

Selection commits before capture. Capture failure or changed metadata does not
undo selection, reuse the consumed token, focus another surface or clear recovery.
Tests cover capture against the new binding, retained results without execution,
failed capture preserving revision/recovery, and changed metadata preserving the
selection record. The no-image route remains available.

The first wider test launch produced no result before storage/WSL failure; its
empty directory/log do not prove tests passed. After recovery a fresh check-02
allocation ran the checks; the GUI trial was not repeated. One separate read-only
WSL launch during setup failed with `Wsl/Service/0x8007274c`; the existing GUI
runner completed normally. Later disk exhaustion prevented evidence packaging.
Neither infrastructure incident is counted as a successful test or task retry.

`raw.tar.gz` retains the original GUI files and fresh check-02 logs. Run
`python runtime/results/review-target-image-01/verify.py` to verify byte integrity,
image delivery, post-selection binding and saved SVG values. Integrity is not
performance evidence.
