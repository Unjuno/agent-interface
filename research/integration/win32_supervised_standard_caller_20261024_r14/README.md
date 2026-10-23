# Win32 supervised standard MCP cancellation under a retained hook block — R14

R14 is a one-shot local Windows trial through the public stdio-MCP caller,
frozen at source `5de12e91bdf8d0d589f429a4f0d3eb422ef2111a`. It extends R13 by
keeping the probe-owned low-level hook callback blocked for 650 ms after the
public cancel response. During this interval the probe polls the exact call ID
and takes a separate-process Q-state sample. This tests whether confirmed release
and independently observed Q-up are available while native input handling remains blocked.

The callback has a fixed 1500 ms self-release cap. A PASS requires same-call
`recovered / release_confirmed=true` plus separate-process same-generation Q-up
while the callback is still held, with the probe recording a full 650 ms hold.
Afterward the probe records exact producer exit, recovery-UP ordering, final
readback, R14 fixture effect, and session close. If release is only confirmed
after callback return, this experiment fails its blocked-I/O question while
preserving those later observations. Every response and event remains in raw
evidence. Any mismatch is FAIL_OR_UNKNOWN; no replay or rerun.

Only this authorized Windows PC and one owned fixture are used. No WSLc or
Docker allocation is used. Runtime `task_success` remains unclaimed. The result
cannot establish MAP01, matched efficiency, broad reliability, or transfer to
other platforms.
