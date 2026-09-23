# Fixed-v9 pointer caller: first integration readiness

Follow-up: [OpenTTD/Mindustry integration](POINTER_DOMAINS.md) now runs both game
adapters with live expired-request/cancellation checks and scripted task scores.
The Inkscape-only scope below describes the first cohort; no paired gain follows.

`pointer_socket_entry_v1.py` wraps existing domain entry points with the unchanged
socket11/cursor5/once-only writer. It selects Inkscape `interactive_v11`, OpenTTD
`interactive_v2`, or Mindustry `mindustry_build_interactive_v1`; it does not replace
their session_v9 backend or task oracles. **The first cohort ran only Inkscape.**
The linked follow-up adds limited game integration/stress evidence; this is not
the completed three-domain performance comparison.

`pointer_exchange_v1.py` takes an explicitly received batch and explicit steps.
Within one caller invocation it persists a clock request, checks the returned
sequence against the referenced image, persists the program request, sends once,
and waits for that program's terminal. It returns full replies, a validated local
image reference and continuation data only after a resolved program boundary.
This removes the need for a separate model decision solely to copy a clock value;
it does not choose actions or render images by itself.

The legacy runtime does not emit modern delivery/admitted-request lineage. The
caller therefore verifies the own transport ID on the echoed command, rejects
an intervening command before the clock, and requires own admission and terminal
after the submitted command echo. It retains the stream prefix. This is a local
ordering check, not authenticated or durable request identity. A clock refresh
does not refresh the image, change observation sequence or add newer runtime31
evidence semantics. Ordinary v9 latest-sequence/focus/lease checks still apply.

## Actual readiness evidence

[Cohort](results/pointer-caller-01/audit.json): the assistant inspected the initial
Inkscape image, then the caller issued a click at the rectangle, a short Right hold,
Ctrl+S and a bounded quiet wait. A prior caller invocation performed observation
only. Two admitted programs completed and released inputs; nine exact AIT frames
reconstruct their referenced PNGs. The saved SVG has x=52, y=50, width=40, height=30
and matches the independent legacy task evaluation.

The archive combines initial read, both callers' clock/program replies and final
evaluation into **all 39 runtime records in order**, without prefix omission.
The runtime/bridge process exited with status zero. It inherits the older desktop
entry point, which does not provide a structured per-child cleanup report.

Ten recorded-reply controls include valid flow, wrong clock echo, interleaved
clock command, changed sequence, gap, timeout, invalid cursor, wrong terminal,
unattributed rejection and transport exception. Unresolved cases retain diagnostic
requests/replies and produce no continuation batch or automatic input retry.
These are mocked protocol controls, not concurrent live cancellation tests.
New wrapper/caller source hashes were captured after this exploratory run;
the original domain manifest is also archived. No token or speedup claim follows.

## Run in the prepared Linux environment

```sh
python3 -u research/live_control/pointer_socket_entry_v1.py inkscape serve -- \
  --app inkscape --seed 991051 --out /absolute/new/run --presentation full
```

Read the emitted socket endpoint and obtain/persist its initial observation batch
using the existing socket read protocol. Inspect the referenced image. Then:

```sh
python3 research/live_control/pointer_exchange_v1.py SOCKET BATCH_JSON RUN_DIRECTORY \
  NEW_PROGRAM_ID EXPLICIT_STEPS_JSON --lease-ms 30000 --out NEW_CALL_DIRECTORY
```

The report's image reference can be passed to the existing combined result/image
display recipe. That display integration was not exercised in the same live
action-return call here. Current JSON stdout repeats replies in diagnostic and
continuation fields; no compression or token savings are established. A result
named `terminal` can still carry failed/cancelled program status and is never an
independent task-success claim. `program_sent` means forwarding may have been
attempted, not that the runtime accepted input. On uncertainty, inspect persisted
requests and stream state; do not call again with a fresh ID to guess a retry.

The client performs at most two exchanges, each with bounded I/O; this is not a
hard end-to-end wall-clock deadline. A batch limit or legacy unattributed rejection
requires reconciliation. Busy/partial writes inherit existing transport limits.
Full adversarial JSON validation, simultaneous-client interference, image-file
mutation, stale action/cancellation/expiry cross-domain tests and latest-stack
integration are still open. Preserve this v1 evidence when changing semantics.

Recheck archived Inkscape records and controls with
`python3 research/live_control/probe_pointer_exchange_v1.py`. Next execute the same
adapter on OpenTTD and Mindustry, add the remaining live boundary/stress gates,
then pin all sources/settings before actual counterbalanced caller comparisons.
