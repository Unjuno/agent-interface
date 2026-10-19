# Fake X lifecycle check/use discriminator r01

This is one synthetic composition experiment for the still-open visual target
binding family (#5). It deliberately schedules `DestroyNotify` after the public
caller's final local press check and cleanup-obligation prearm, but before the
first XTEST press. A separate lifecycle query drains the event and retires the
reader in that interval.

Run the receipt runner under ordinary and optimized Python, then run the full
window-lifecycle module in both modes. Exact raw command bytes are kept as
deterministic `.gz` files beside the parsed JSON receipts; `SHA256SUMS` covers them and
`conditions.json` freezes the setup.

This schedule demonstrates that the first press can be emitted after the
reader has retired; the later press is refused, the prefix release is emitted,
and Fake X keymap readback is empty. It is a counterexample to atomicity across
that check/use gap in this synthetic schedule. It does not establish actual X
server event order, physical release, application effect, successful task
completion, or any live desktop result. `task_success` remains null and replay
is denied. Issue #5 stays open with this residual recorded.
