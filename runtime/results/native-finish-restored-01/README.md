# Restored finish_after: primary last-stage repeat

The primary assistant repeated the failed two-stage Inkscape task with seed
991123 and max_stages=2. It viewed the initial image, moved six right chords,
viewed the next image, then moved twelve chords and saved with finish_after.
Both immutable request files are byte-identical to the failed run's requests.

This time stage 2 returned finished with its action, final image, successful
evaluation and completed cleanup. No source-3 was published. Independent SVG
inspection confirms x=86/y=50/width=40/height=30 with no transform. Both programs
verified empty release. Owner 19034 returned code 0 and EOF closed relay exec
92562 with code 0. The former stage-exhaustion failure remains in the prior
archive on commit 96e150f03; it has not been rewritten as a success.

Run `python3 runtime/results/native-finish-restored-01/audit.py` from the repo.
The audit verifies the manifest, exact requests versus failed-run copies, reply
digests, image bytes, saved geometry, absence of an extra stage/error, release,
evaluation, cleanup and owner exit. PLAN.md precedes allocation; provenance
records source and process IDs. The manifest predates audit.py and this README.

This is scoped WSL live composition after restoration. It is not a container
experiment, general reliability estimate, latency comparison or token/cost
result. A temporary relay driver supplies transport only; primary decisions
were made after viewing images. No sensor changes were made. Process exit and
cleanup scope remain distinct from verification of every possible descendant.
