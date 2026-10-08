# Click-to-text readiness intake

Decision: **HOLD automatic zero-gap click/text batching as a validated recipe**.
This intake adds no runtime delay and no new sensor. The public paced-dispatch
primary trial lost its first `h` and repaired it explicitly; see
[the retained primary evidence](../public-paced-brief-01/README.md).

## What the existing experiment actually exercised

[PR #4053](https://github.com/Unjuno/agent-interface/pull/4053) retains 30 cases:
12 correct A effects, 15 wrong B effects and three no-input controls. A fresh
read-only restoration verified all 367 capsule files (12,241,141 bytes), the
original raw-only audit passed, and all 13 auditor tests passed. No GUI/formal
allocation was repeated. `intake.json` pins the capsule and inspected source.

In the retained `run.py`, the activation program returns before
`snap('after_activation')` and `snap('before_text')`; only then does the separate
text program start. Both snapshots call the cooperative app's `observe` RPC.
In `app.py`, every command schedules its response through
`root.after(15, finish, command)` so the ordinary Tk event loop can run.
The B-after-activation cases additionally change focus through another RPC.
These app turns and recipient snapshots are part of the tested conditions.
They are not present in a single public click/text program.

The six stable/before-activation click cases saved the intended digit and had
35.229–42.887 ms between activation return and text start. The three
B-after-activation cases had 54.882–56.043 ms and still typed into B.
`click-boundaries.json` retains each exact integer timestamp and final values.
These are historical diagnostic intervals, not a recommended wait duration,
minimum safe delay, latency benefit or causal explanation of the primary failure.
A delay does not protect against a later focus change.

## Integration decision

Keep ordinary click recovery as an explicit caller choice under current geometry
and recipient evidence. Do not interpret X-server synchronization, successful
window activation or a capture as acknowledgement that the intended editor has
consumed the click. Existing `wait_update` can provide an explicit fixed delay,
but its receipt correctly does not claim an observed update. Review the entered
value before a consequential save/submit; a mismatch needs an explicitly authored
repair rather than replay of the whole uncertain program.

[Issue #4061](https://github.com/Unjuno/agent-interface/issues/4061) studies a new
cooperative receiving-app capability. Its latest recovery comment reports that
only the freeze is retrievable and the full raw/source capsule is unavailable.
The historical PASS is not treated here as independently revalidated evidence,
nor as a generic XTEST feature ready for integration.

Next candidate evaluation must preserve the distinction between a batched
click/text program, an explicit fixed-delay program, and an application-owned
readiness acknowledgement. Use a fresh allocation with identical task/environment,
retain first-character losses and wrong-recipient effects, and measure added waits
and recovery calls. No default or universal readiness contract is promoted here.

## Read-only reproduction

From the repository root, run:

```sh
python3 -O runtime/results/click-readiness-intake-01/verify.py
```

The verifier reads pinned Git objects, restores the capsule in a new temporary
directory, runs only its auditor, checks exact derived click boundaries and
confirms the documented RPC boundary in the pinned sources. It never launches
the GUI runner. Retained `tests.stderr` contains the original 13-test re-audit.
