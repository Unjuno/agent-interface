# X11 observer reconnect key-state boundary — Issue #4135

## Result

`PASS_RECONNECT_KEY_STATE_BOUNDARY_SCOPED` for allocation `x11-reconnect-key-state-20260922-02`.

The first formal allocation remains separately `STOP_EXTERNAL_TOOL_TIMEOUT / HOLD_FORMAL_INCOMPLETE`: seven complete cases, one partial-start case directory, no batch terminal receipt, and no retained outer return code. None of those v1 rows are pooled into v2.

| Policy | exact lowercase `b` | wrong uppercase `B` | unresolved |
|---|---:|---:|---:|
| `CARRY_OLD_STATE` | 8/12 | 2/12 | 2/12 |
| `REBOOTSTRAP_ON_RECONNECT` | 8/12 | 0/12 | 4/12 |

The four candidate unresolved rows are the preregistered `NO_BOOTSTRAP` and `WRONG_EPOCH_BOOTSTRAP` controls and are required fail-closed outcomes, not task successes.

## H / T / D / C / U

- **H:** a new observer connection has no justified event history before that connection. Carrying the old observer's Shift state across a disconnect can therefore be wrong. A current X-server key-state bootstrap bound to the new observer epoch, followed by only new-epoch events, should repair the directed cases; missing/foreign bootstrap must remain UNKNOWN.
- **T:** private authenticated TCP-disabled Xvfb, CPython 3.13.5, Tk, Python-Xlib/XTEST. Two policies × six schedules × two repetitions = 24 fresh Entry sessions. Two formal allocations are retained: v1 stopped at its outer execution envelope; v2 changed only outer serialization to six four-case batches. No model/provider, user desktop/data, package install, or experiment network.
- **D:** v2 completed 24/24 cases; six batch runner exits and six independently retained outer exits are zero. Raw-only audit: 233 checks, errors `[]`. Twelve copied-evidence mutations reject after intact copies pass. Ten policy unit methods pass. Eight frozen scientific source/plan hashes are unchanged.
- **C:** cooperative one-key Tk/Xvfb fixture, explicit reconnect barrier, serialized writer activity. Bootstrap is X-server logical state, not physical HID history or timeless authority. It does not detect silent loss automatically and is not atomic with future input.
- **U:** arbitrary toolkits, grabs, multiple modifiers, lock/IME/layout state, reconnect under concurrent mutation, natural failure rate, production integration, model utility, latency/token savings, cross-platform transfer and product readiness remain untested. Same-author separate raw auditor is not external human review.

## Directed counterexamples

When Shift was pressed while no observer was connected, `CARRY_OLD_STATE` retained UP and typed uppercase `B` in 2/2 rows. `REBOOTSTRAP_ON_RECONNECT` sampled DOWN on the new epoch, waited for the subsequent release event, then typed exact lowercase `b` in 2/2 rows.

When Shift was released while no observer was connected, `CARRY_OLD_STATE` retained DOWN and remained unresolved in 2/2 rows. `REBOOTSTRAP_ON_RECONNECT` sampled UP and typed exact lowercase `b` in 2/2 rows.

A missing or foreign-epoch bootstrap never authorized task input in candidate rows.

## Construction and retained failures

Three construction-only defects were found before the first public freeze: inherited Xauthority in the runner's own Xlib connection, incorrect serialization of Python-Xlib `query_keymap()` output, and bytes-valued stderr in the final evidence JSON. All are retained and excluded from the scientific denominator.

Formal v1 then consumed its first 12-case batch but the external execution tool timed out after seven complete cases and one partial-start case. The batch terminal receipt and outer return code are absent. The allocation was not retried. V2 was separately identified and publicly frozen under the same Issue before any v2 formal case; its only scientific delta is none—only the outer batch size changed from 12 to 4.

## Verification

Read-only publication verification:

```sh
python -B verify_publication.py
```

This restores the retained archive into a fresh temporary directory, checks member hashes/counts, re-runs only the raw audit, copied-evidence controls and unit tests, and never starts Xvfb or executes a consumed formal case.

## Integration meaning

A reconnect is a new observation epoch. Old reducer state is not evidence for events that occurred while disconnected. Before using the new stream, either establish a current bootstrap bound to that epoch and then apply subsequent events, or remain UNKNOWN. This is a scoped evidence constraint for #2107/#57/#2789, not a production runtime change or integrated/product PASS.
