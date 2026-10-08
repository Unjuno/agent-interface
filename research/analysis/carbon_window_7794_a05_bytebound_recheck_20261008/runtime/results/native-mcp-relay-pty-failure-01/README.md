# Failed primary relay transport: Windows PTY redraw

The sequential relay passed ordinary pipe tests, but primary use through a
Windows interactive terminal failed to deliver parseable image JSON. ConPTY
inserted cursor positioning, wrapping and duplicated display characters.
Removing escape sequences/newlines did not restore JSON. No image was accepted
and no movement/save action was attempted.

The primary sent an explicit no-input finish to the same allocation. The
retained request is source_sequence=1, finish=true. Task evaluation is false
(shape remains x=50), while cleanup reported completed. Read-only status showed
owner 17670 terminal/code 0; EOF then closed relay exec 44853 with code 0.
Independent ps found no owner process. There was no restart or replay.

pty-raw.json retains start/finish output and parse failures. allocation retains
the harness records. PLAN.md precedes allocation and relay.py captures candidate
source. manifest.json hashes these files before this README. Final status and
ps output were inspected in the task, not retained in the archive.

This is failed transport evidence, not successful primary relay control. Keep
the relay experimental and use a pipe-preserving host connection. Do not infer
latency, cost or tool-call benefits from the successful pipe protocol tests.
