# V39 session JSONL child-pipe composition A01

## H — hypothesis

The exact `session_map01_v12.emit` serializer and V39 controller `reader` and
`wait` functions preserve one retained cancellation-cleanup `input_released`
row, including both owner per-key brackets and explicit no-authority state,
when those functions communicate through an actual Python child process and
stdout pipe. This tests the process/pipe boundary missing from the in-memory
source-composition A09 result.

## T — test

Extract the exact function ASTs from the frozen synthetic composition tree in
`FREEZE.json`; launch a one-shot Python child that calls the exact extracted
`emit` function with the byte-pinned A08 event. The parent runs the exact
extracted `reader`/`wait` functions over the child's real `stdout=PIPE` and
checks the received decoded row against the input event, permitting only the
expected added integer `emit_ns`. Verify one stdout line, one writer event,
one delivered event, empty stderr, no reader error, child exit 0, two nested
per-key release records and authority false. The only child writes are to a
fresh package-local output directory.

This is an offline, one-process construction run. No session `main`, VizDoom,
planner, X server, GUI, OS input, shared container, GPU, or user application is
started.

## D — decision

`PASS_CHILD_PIPE_TRANSPORT_SCOPED` requires every condition in T plus exact
source/input identity. A semantic row change, duplicate/missing row, false
authority, child/reader failure, or nonempty stderr is `FAIL_TRANSPORT`; source,
runner, or environment mismatch is `HOLD_CONSTRUCTION`. Run once; do not repair
or retry this frozen candidate.

## C — competing explanations

This may prove only that the isolated serializer functions and actual OS pipe
transport preserve an already-constructed event. It can pass while the actual
session entry path never emits that event, while executor ownership fails, or
while the game does not consume the input or produce useful feedback.

## U — uncertainty and scope

The synthetic event was previously produced by fake/source-level cancellation
cleanup. This test does not invoke the real V39 session main, executor, input
owner, X server, ViZDoom, model, or user desktop. It says nothing about
independently useful feedback during planner latency, bounded recovery,
threat-response efficacy, matched outcomes, safety rates, or MAP01 completion.
