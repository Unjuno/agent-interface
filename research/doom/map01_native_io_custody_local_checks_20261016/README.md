# Current MAP01 native-I/O failure custody: Fake X only

The actual selected backend/Executor/V4/V12 path could emit a failed terminal
with unverified release, empty its active slot, and accept another program.
First RED on base `8961cc8f61e0dbf65f832f6e7a067c79dce4bbaa` plus the initial
regression reproduces all four fault cells (`first-admission-red.log`). This was
ordinary local regression development, not a formal/live allocation.

| Stalled primitive | Fake state at unverified terminal | Late exposure |
|---|---|---|
| Initial KeyPress send, before delivery | No key down yet | Original pending press may still deliver after cancellation |
| KeyRelease send, before delivery | Keycode 38 remains down | Original release has not returned |
| Sync after KeyRelease | Fake key map empty | Sender lacks confirmed completion |
| Keymap readback after KeyRelease | Fake key map empty | Cleanup cannot verify its empty state |

The original owner request wait expires at its existing two-second cooperative
policy, cancelling the lease and retiring the owner from new API requests. It
does not preempt the native call. The test retains the blocked primitive until
after the failed terminal; native calls run only against Fake X objects.

## Repair and evidence

Executor V12 (inherited by V13) now retains its first unverified terminal release
as a deep-copied obligation before external terminal publication. It includes
the original ID, intent token, deadline, observation sequence, selected target
process identity and release result. The terminal carries
`input_recovery_required` and the obligation. Later submission refuses before
validation, source binding, ID consumption or `accepted`. Snapshot access returns
a copy. Fresh observations, late native return and eventual owner cleanup do not
clear the obligation or renew input authority.

The four-cell regression uses actual capture/publication, selected backend,
Executor, V4 and V12 with patched fake native primitives. A fresh observation
after failure cannot enable a second admission. It checks the frozen source,
copied custody, no positive replay, eventual empty fake state and stopped owner
after the harness resumes the original call. Each JSON row in the normal/-O test
log retains the stalled state, actual terminal and final obligation. A separate
healthy control runs two programs with verified cleanup and permits ordinary
subsequent admission.

Clean source `9aba72cad1cb00a0088b78c37e19920b4388079e`: the isolated runner
checks 34 modules / 251 methods in each normal and optimized mode, zero failures,
one deliberate real-Codex handshake skip (250 executed). One method contains the
four fault cells; these are not four independent live trials or reliability data.
Bounded read-only review of runtime source at `28597691fd52036aebfc6a990c50572222e18b88`
found no actionable issue; subsequent code only fixes test construction.

The first sweep exposed two old stale-admission tests that bypassed `__init__`
using `__new__` and manually copied partial state. Their first failure and summary
are retained. They now use the actual constructor with the same assertions and
fake backend; no production compatibility fallback hides missing initialization.

`normal/` and `optimized/` retain every module log and summary. Commands use
`../check_map01_control_regressions.py --output-dir <fresh path>` and add
`--optimized` for the second mode. Windows, Python 3.13.14, python-xlib 0.33,
Pillow 12.2.0, MCP 1.30.0, openpyxl 3.1.5. `MANIFEST.json` hashes retained files.
No GUI/display/game/container/model/WSLc allocation was launched.

### Standard session rejection follow-up

Caller inspection found that the initial `RuntimeError` refusal would escape
session V12's per-command rejection handler. The fence now raises `ValueError`,
which that existing handler reports as `rejected`; no session exit or new input
is required. `protocol-normal/` and `protocol-optimized/` retain the final runs
at clean `64b830fb019fb6a5ebe8b47b822aedf371a536f3`: both 34 modules / 251 methods,
zero failures, one deliberate handshake skip. Earlier runs above remain intact.
Bounded correction review confirms the caller catch path and all 22 drain tests.

## Remaining requirements

This is an Executor-lifetime reuse fence, not native-I/O interruption, physical
release, or a recovery protocol. It does not protect replacement processes or
sessions on the same display. The original input writer retains cleanup custody;
no second writer is introduced. The test explicitly allows one in-flight press
to arrive late and only proves absence of a new positive replay. The reader/focus
isolation in #8950/#8952 cannot bypass server-global stop, as #8953 preserves.

Do not clear the obligation based on a screenshot, caller timeout, an unrelated
release, or task completion text. A future explicit handoff/recovery must establish
original resource/owner retirement, verified release and fresh authority without
replaying unknown effects. Independent task effect, finite task recovery, window
incarnation, atomic server acceptance and matched efficiency remain open in
#17/#59. Historical raw and first outcomes remain unchanged.

The outer V39 `cancel_invalidated_action` still waits specifically for
`input_released` before terminal closure. Its failed-terminal/unverified-release
classification needs a separate composed fault check; this Executor fence does
not qualify that outer wait as bounded recovery.
