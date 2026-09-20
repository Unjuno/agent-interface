# Current production CLI: fresh Calc primary use

Primary-assistant use of source `2dff80852292cc82fd5c23a449c8244bea94bc25`
saved Quantity / Unit price / Total, values 8 and 19, and formula `=B2*A2`
with numeric result 152 in a new isolated WSL/Xvfb Calc task. This follows the
retention, attempt-status, short-write and flush integrations. The assistant
viewed each recorded image before choosing the next action. No subagent or sensor
was used. The runtime CLI ran outside checkout with explicit retained directories.

Two dispatches closed the visible startup tip and entered/saved the table.
Three observations covered initial setup, the fully drawn startup dialog, and
the final result. The entry/save dispatch returned completed with verified input
release, but its image still showed Saving/intermediate UI after the explicit
50 ms final wait. The assistant requested one final observation, saw 8/19/152,
and ended the run. There was no input replay. Saved FODS independently contains
`of:=[.B2]*[.A2]` and value 152.

This preserves another instance of the useful-feedback gap in
[#3700](https://github.com/Unjuno/agent-interface/issues/3700), not its formal
Docker 50/250 ms comparison. No larger default wait, token/cost reduction,
human-speed equivalence, or performance improvement is established.

## Retained evidence and read-only verification

`evidence.tar.gz` contains 69 files: exact raw requests/reports, commands,
primary decisions, screenshots and stdout image payloads, initial/final FODS,
timings, harness, cleanup, source hashes, and the exact portable candidate.
`manifest.json` and `archive.json` bind individual files and the archive.
The original local files and their frozen hash inventory were preserved.

Run `python verify.py` from any directory with Python's standard library. It
reads the archive without extracting it or executing its runtime/harness. It
checks exact file hashes, five request/report pairs, image/presentation equality,
two completed dispatches and recorded releases, saved headers/formula/value,
and recorded cleanup. Expected: `PASS_RETAINED_CLI_RECORD_CONSISTENCY`.
This proves record consistency, not independently the assistant's image judgment
or live process state. PNGs preserve the intermediate and final states for review.

The candidate SHA-256 is
`aa9024a5eea4384bdbba349b907f9f2a279ca2d041e50418a7820e778591aae0`.
Historical harness paths reference the original sibling delivery directory;
the bundled `candidate/runtime.pyz` is for inspection, not an automatic rerun.
The harness explicitly refreshes a private-test 10-second lease after each
primary decision; it does not establish server-issued freshness. Original timing
rows measure CLI process roundtrips only, not model-useful feedback latency.

Owner exited 0. Tracked Calc launcher/Openbox/Xvfb returned 255/0/0 during
cleanup, and recorded process-group member paths were absent afterward.
Full descendant closure was not verified; the retained document lock file is
not proof of a gracefully closed application. No Docker repair or restart occurred.
