# Bounded passive followup read

bounded_followup_v2 reconstructs PendingAction from recorded received exchanges, requires verified input_stopped_capture_pending, and makes one read-only terminal poll. Server wait is 400ms; the socket exchange has a 650ms absolute I/O deadline including connect/send/receive. It does not send a command, retry input, renew a lease, or loop. A response timeout remains pending; socket timeout/EOF/error is recorded without advancing the received cursor. Existing early notification timestamps stay in the original exchanges.

A terminal arriving within this wait is folded into the report. Only previously received image references are resolved; unavailable images are reported separately from lifecycle completion. This does not certify readiness, saved task effects, current focus or input authority. Report copying, JSON processing and local image/hash operations are outside the socket deadline, so 650ms is not a hard bound on the whole Python function.

## Preserved failure and measured tests

- bounded-followup-01: v1 failed after receiving terminal because the synthetic fixture observation had no image reference. Exception and exit 1 are recorded in failure-note.json; the incomplete report remains unchanged. This prompted v2 to return image unavailable independently from terminal state. No fabricated image or task success was substituted.
- bounded-followup-02: actual private socket and synthetic blocked-capture process. The first bounded read returned timeout/pending in 401.166ms; the cancellation socket still replied; after gate release a bounded read returned terminal/stopped with one capture in 16.951ms. Six exchanges/eleven raw events matched contiguous history; exit 0.
- bounded-followup-03: same controlled transport without cancellation. First read timed out/pending in 401.086ms. On a later bounded read the gate was scheduled to release after 180ms; both passive samples finished and terminal was returned in 290.876ms, inside the 400ms server wait. Five exchanges/ten raw events matched; exit 0. The printed early_notification_before_gate_release value here compares against timer scheduling, not the delayed file write itself; the earlier blocked phase independently establishes early receipt.
- followup-io-01: a separate real AF_UNIX peer accepted the read but sent no response. The helper returned TimeoutError evidence in 668.309ms wall time including local overhead, preserving cursor and pending state. Exactly one command-free request reached the peer; peer thread joined.

These are controlled transport probes, not new Calc episodes or model latency measurements. Synthetic runtime observations intentionally omit images; unavailable output remains visible. No default is promoted, and no absolute capture or whole-function deadline is claimed.

## Next integration

Wrap early_exchange with at most one bounded_followup call inside the same outer client operation. Keep raw early receipt and outer-return timings distinct. A short natural Calc transition may then avoid an extra model turn while a slow capture can still return pending. Run the same GUI task with this combined path, and address the receipt's unsupported lifecycle/state names before adoption. Do not hide pending/error evidence to make formatting look complete. Repeated familiar-task wall time is not a causal performance claim; actual model token/cost measurement remains open.
