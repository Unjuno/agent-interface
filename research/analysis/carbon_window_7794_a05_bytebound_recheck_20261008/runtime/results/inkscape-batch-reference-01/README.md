# Explicit prior-result reference in Inkscape self-use

The assistant used literal stdin JSON with `batch_file` for two actual programs
in private Linux/X11 Inkscape, seed 991076. No action request or steps file was
generated between decisions. First it viewed the initial red rectangle, clicked
it and settled. The returned image showed X=50, Y=50, W=40, H=30. The assistant
then explicitly referenced that program's report, clicked the visible X field,
entered 80 and saved. Final image and independent saved-SVG evaluation showed
X=80 with unchanged Y=50, W=40, H=30 and no transform attribute.

Both programs completed with verified empty key/button release. There were five
socket exchanges before cleanup; independent evaluation arrived directly, so
the final drain correctly made no extra read. Explicit finish closed the server
with exit code 0. Viewed sequences were 1, 6 and 16.

This verifies source-reference loading and pointer/numeric-field workflow in
one additional desktop app. It is not a matched speed, token or reliability
benchmark. The caller still chooses the source file, socket, directory, actions
and output path. A file reference is not proof that a model viewed its contents,
and it grants no fresh input authority. Raw source batches are retained in each
attempt; display views are rejected as incomplete source objects.

Evidence: `runtime/` contains original frames, deliveries, source manifest and
saved SVG; `select/` and `move/` contain full preparations and network requests,
replies and reports; initial and cleanup replies are at the top level.
`client-source/` captures the used client code. Outer stdin requests are recorded
in conversation, not claimed as separate raw artifacts here; selected filenames
are recorded in `SUMMARY.json`. Historical paths are unchanged. `SHA256.json`
covers evidence before this README. Fourteen client/review tests passed on
Windows and WSL, including source conflict, incomplete view and snapshot tests.
