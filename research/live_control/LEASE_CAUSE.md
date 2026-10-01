# Per-intent interruption evidence candidate

Inspection found all current owner versions through v9 and sessions through v21
still depend on executor_v3, which discards DecisionRequired text. Some newer
branches provide text (held-button loss, continuation deadline), but it never
reaches the terminal. The asynchronous release record is separate from final
cleanup, so reading the global last release cannot identify the affected intent.

Candidate components:

- `lease_cause_v1.py`: a unique token and copied first interruption record on each
  Lease instance. Equal deadlines do not share cause state. Ordinary release/close
  records do not replace the cause. Snapshot mutation cannot alter stored evidence.
- `input_owner_v10.py`: preserves v9 behavior, adding an optional recording call on
  the active lease before appending a release record or clearing ownership.
- `executor_v4.py`: preserves v3 exception identity for existing backends, uses the
  new Lease, retains DecisionRequired text, and adds interruption snapshot to the
  terminal after cleanup. Final release verification remains independently visible.

Existing measured versions remain unchanged; no default fixture is switched. An
integration must choose both new executor and owner explicitly. A v3 lease does not
record causes even with owner v10. A v4 executor cannot infer causes from owner v9.
The cause is the first recorded owner interruption, not proof of a unique physical
root cause. Null means unrecorded/unknown, not absence of interruption. Guards can
raise DecisionRequired without an active hold/release, so not every path has a cause.

The synthetic probe exercises actual executor threads with controlled owner-release
records. It verifies first cause preservation, copied snapshots, isolation between
distinct same-deadline intents, retention of exception text, and independent final
cleanup. The second successful intent has no inherited cause. Owner v10 was compiled
but has not been exercised against X11; this probe does not prove live integration.

Run `python3 research/live_control/probe_lease_cause_v1.py`; evidence is
`results/lease-cause-01/report.json`. Next use private Xvfb windows to induce actual
focus transfer during a held input and verify the terminal's cause belongs to that
lease, input releases, and a subsequent intent does not inherit it. Include normal
completion and preserve failures. No latency or model-performance claim yet.
