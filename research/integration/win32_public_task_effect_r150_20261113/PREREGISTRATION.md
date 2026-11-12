# R150: public task oracle after native queued effect

H: the existing public supervised Win32 task verifier can attach an independent
late counter-effect receipt to the exact recovered action without rewriting
input-release/cancellation scope or granting replay authority.

T: one fresh owned fixture on the authorized PC. Use the retained R149 queue
protocol in BASE_QUEUE_PROTOCOL.md: A down, 50 ms hold, A up, 15 s wait, authority
4 s from the public clock, automatic recovery with a 2 s horizon, 650 ms extra
queue hold after terminal, and 500 ms effect tail. Maximum hold 20 s and fixture
lifetime 180 s. Preserve exact-call polling/fallback limits from that protocol.
R149 itself is not replayed. Material change: trusted server-side counter oracle,
one public interface_verify_task call after the late effect, and retained-result
inspection. No model calls, runtime downloads, Docker or WSL claim.

Before input, preflight obtains the exact owned fixture's current generation
through the native read-only observation facade. It verifies unchanged custody
and saves a server config in a new file. The runner reobserves and refuses a
generation mismatch. The client supplies only the exact call ID to verification.

D: require all inherited queue/recovery checks AND all public-effect join
checks: verified success, matching call/operation/generation, fresh observation
inside the oracle reservation/receipt window, effect time after original recovery
terminal, exact source hash/rows, retained task_effect, unchanged original action,
and replay denied. The artifact must be within the packet with the oracle-ID
filename. Bound reads to 65537 bytes and reject over 65536. Missing or malformed
evidence is not a PASS. One verifier attempt, no retry or success relabeling.

C: a server configuration is not proof of a live observation; retain the
preflight report and independently compare the runner's generation. A counter
file can be stale or from a different fixture; bind nonce and fresh target,
preserve source event time separately from the oracle read time. Late or
duplicate effects, target changes, timeout, and uncertain release remain failures
or UNKNOWN under the inherited criteria. No threshold change after results.

U: deliberately filtered fixture, one formal dispatch. This does not establish
application quiescence, arbitrary late OS delivery, MAP01 completion, reliability,
general 20 ms behavior or same-model economics. Keep all first outcomes/raw.
