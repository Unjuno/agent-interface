# MAP01 recovery stage attribution R153/R154 (2026-11-13)

## Question and decision

R151 failed the fixed 20 ms expiry-to-neutral outer key-read bracket at
22.3277 ms and retained 7.9521 ms between recovery-exchange entry and helper
recovery entry. R152 measured 2.3694 ms for that exchange-to-helper interval,
including a 2.2465 ms bounded send call, and did not reproduce the R151 interval.
The narrow question was whether a fresh public-call-path run could join the
helper lock, process identity/liveness, parent/child pipe, send, and recovery
stages without changing input or recovery behavior.

R153 stopped before any input because the exact-window foreground changed back
to Codex before its external CUA receipt reached the runner. The strict gate
rejected the stale foreground claim, then closed only its owned GZDoom process
normally. R153 is retained as a pre-action orchestration failure; it is not a
recovery trial and was not retried.

Fresh R154 passed one instrumented public compiled-supervised native Win32
MAP01 attempt. Its conservative outer expiry-to-neutral QPC bracket was
**10.0353 ms**, below the unchanged 20 ms limit. W remained observed down for
7.9999 ms after expiry; the first up read fully after expiry was 9.2503 ms after
the serialized deadline. Independent same-generation readback confirmed W and
mouse-left neutral, followed by a verified two-second horizon with 77 samples
and no read error. The expiry sampler retained 6,953 samples and was healthy.

The independent task oracle joined the same public call, operation, and target
generation and measured the exact ammo change **50→49**. Fresh-capture/public
receipt timing passed. Same-run demo adjudication was
`PASS_SCOPED_NO_RECORDED_FORWARD_COMMAND`: no recorded forward command occurred
in the conservative post-release demo interval. That does not exclude queued
Windows messages, other input types, or scheduled effects; MAP01 completion was
not claimed.

## Stage trace

All three process trace files used QPC-backed monotonic and performance clocks,
reported zero dropped spans, and joined the operation, generation, recovery,
and request identifiers. The lock, process identity/liveness, send, both pipe
directions, and recovery-entry checks all passed. Deep attribution was
`attributed`:

| Interval | R154 |
|---|---:|
| Exchange entry → helper recovery entry | 1.1148 ms |
| Lock acquisition | 1.8 μs |
| Lock return → send start | 20.7 μs |
| Bounded send call | 1.0115 ms |
| Send return → helper receive completion | 48.3 μs |
| Helper receive completion → recovery entry | 25.7 μs |

These are instrumented software-stage timings, not physical input-delivery
timestamps. R154 did not reproduce R151's 7.9521 ms interval. The differing
single-run values do not identify the cause of that delay and do not justify a
runtime behavior change, speed claim, reliability estimate, or hard latency
guarantee.

## Provenance and next work

R154 used main `49dd39a89b0b2d4becbe3df0ff3273b2f1d3b0ab`, which includes the
request-correlation trace fix from [PR #10263](https://github.com/Unjuno/agent-interface/pull/10263).
Ten packet tests passed normally and under `python -O`; the frozen source,
runtime, asset, and custody verification passed all 57 checks. The exact owned
GZDoom process exited normally after release verification (exit 0, no forced
termination), and durable custody is clear.

Raw conditions, first outcomes, public receipts, key samples, demo, images,
traces, and additive adjudications remain in the task-local packets
`map01_native_windows_deep_trace_20261113_r153` and
`map01_native_windows_deep_trace_20261113_r154`. Their finalized manifest
SHA-256 values are respectively
`b539be9a1db5e1cad5ea4005d22b8d779fe1975899d9d15733f3c03ff4ef6beb` and
`6a2362836dbb655e053b7776d658718cc886765db6eb0c4fe6c09f965ab35368`.
R154 frozen conditions SHA-256:
`baad06eb060b6f3de5b79e1c3d89f353b1d7e07766863a29bee3101eb21c18fa`.

The open research question is why R151's longer exchange interval occurred and
whether its tail recurs under the same instrumented public path. R154 is one
qualifying sample, not a matched estimate. Continue with bounded, independently
identified runs only if needed to characterize recurrence; preserve each first
outcome and keep the 20 ms gate unchanged.
