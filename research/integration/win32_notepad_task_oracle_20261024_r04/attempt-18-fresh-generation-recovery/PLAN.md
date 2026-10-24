# R18 — bounded held-keyup recovery on a distinct target generation

## Question and scope

Does the production supervised-Win32 recovery path release a real SHIFT-down and establish same-generation SHIFT-up when the producer is held after successful native SHIFT-down and before native `SendInput` for SHIFT-up, using the distinct R17 target generation?

This is one recovery-only trial. It reproduces the R13/R14 backend-send-boundary injection on the new HWND/GUI thread, and is not an OS/kernel/API-internal I/O hang, arbitrary blocked-platform-I/O guarantee, task-success test, matched efficiency comparison, broad reliability estimate, stdio test, MAP01 result, or WSLc run.

## Frozen target and stop gates

Use only HWND 370739280 / target `notepad-r18`, whose R17 generation is `3e0505c367c9faf8aac8133e4620a9d1de06ce481d487eb7265906286406888f`, distinct from R16. Before any input require the exact window still exists, is visible/enabled/foreground, the document is blank, SHIFT is up, and generation differs from R16. Public observation must preserve the same generation. Any mismatch exits without dispatch.

## Frozen fault and acceptance

Dispatch public focus, SHIFT-down, SHIFT-up, release-all. The isolated producer sends real native SHIFT-down, then blocks at the backend send boundary before the native SHIFT-up API call. Observe SHIFT-down independently, issue one bounded public cancel, retain terminal and cancellation results, and independently check same-generation SHIFT-up plus unchanged empty document. Require successful recovered dispatch/cancel receipts before the 3 s cleanup deadline, replay denied, and high-resolution interval present. Any uncertain recovery stays UNKNOWN; preserve raw and do not repeat.
