# R19 — simulated SendInput-entry stall during held-key recovery

## Question and scope

Can the production supervised-Win32 cancellation/recovery path release a real SHIFT-down when the producer reaches the `user32.SendInput` call site for SHIFT-up and that call fails to return, using the R17 target generation? This moves fault injection from the next backend send boundary to the API-callable entry boundary.

This is one recovery-only trial on HWND 370739280 / generation `3e0505c367c9faf8aac8133e4620a9d1de06ce481d487eb7265906286406888f`. A Python callable substitutes at the child process's `user32.SendInput` attribute and blocks before invoking the native function for SHIFT-up. The helper uses the real native function to release. This does not create a hang inside native Windows `SendInput` or the kernel, and it is not an arbitrary blocked-platform-I/O guarantee, task-success test, broad reliability estimate, stdio/MAP01/WSLc run, or efficiency comparison.

## Frozen preflight and stop gate

Require the exact target to exist, be visible, enabled and foreground, blank, SHIFT-up, and retain a generation distinct from R16. The public observation must preserve that generation. On any mismatch, issue no program.

## Frozen fault and acceptance

Dispatch focus, SHIFT-down, SHIFT-up and release-all. The child calls the native `SendInput` for SHIFT-down, then blocks at the substituted `user32.SendInput` entry for SHIFT-up before the native function is invoked. Independently observe SHIFT-down, request one bounded public cancellation, and retain the terminal action and cancellation receipts. Pass only if producer retirement is confirmed, same-generation release is confirmed before the three-second cleanup deadline, independent readback observes SHIFT-up, the document remains empty, replay is denied, and high-resolution recovery timing is present. Preserve raw evidence; do not retry an uncertain result.
