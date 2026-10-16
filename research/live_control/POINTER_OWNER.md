# Pointer input owner candidate — 2026-09-13

Follow-up: [geometry and lifecycle candidate](POINTER_LIFECYCLE.md) adds v5,
window-change tests and private-Xvfb failure injection. This report retains v3 evidence.

`input_owner_v3.py` extends the independent X11 owner with absolute motion,
buttons 1–3 and bounded vertical wheel pulses. Two real-X11 probe runs completed
11 and 12 checks respectively. This is a candidate primitive implementation,
**not yet wired into the shared backend/program validator or OpenTTD adapter**.
It does not promote a runtime or add agent task successes to the ledger.

## Added behavior

The existing call shape is retained: `call(operation, lease, payload)`.

| Operation | Payload | Meaning |
|---|---|---|
| `move` | integer `x`, `y` object | absolute root-screen position, bounded to root geometry |
| `button_down` / `button_up` | integer 1–3 | owner-managed press/release; cleanup release does not require a live deadline |
| `wheel` | nonzero integer -10…10 | positive = button 4 pulses, negative = button 5 pulses; vertical only |

Pointer admission requires the lease's observed `expected_focus` and an
additional `expected_surface` client-window ID. The latter is supplied by the
trusted test harness in these probes. A future backend must bind it from the
same observation as the request; it must not accept an arbitrary target ID
chosen by a planner as proof of observation.

The owner walks X11 child windows at the requested point and requires the
declared surface to occur in that path. This addresses a distinction absent
from keyboard input: focus can remain on one window while a pointer action
would hit another. While a button is held, the owner also checks the actual
pointer location against the surface. Focus/surface loss invalidates the lease
and releases held input. Old-lease release cannot release a newer lease's hold.

Keyboard and button cleanup run on the owner's connection/thread, independently
of caller capture/logging work. Button masks and keymaps are queried after
release. Wheel pairs are issued on that same thread and recheck the lease
before each bounded pulse. This is scheduler-dependent X11 control, not atomic
input admission or a hard-real-time deadline guarantee.

## Observed probe results

The tests create two private override-redirect X11 windows and a temporary
overlay; they do not use the user's desktop or any gameplay engine API.

- Motion/held-button motion/release were delivered to the test surface.
- Two upward wheel pulses generated two real press and release event pairs.
- Expired movement, cancelled press, another surface and out-of-root position
  were rejected. The second probe also rejects wrong-focus movement explicitly.
- With no further caller requests, deadline expiry and cancellation released
  button 1, as confirmed through independent X11 pointer state.
- Focus transfer and a covering window that did **not** take focus each released
  the held button; the corresponding owner-release reasons were recorded.
- An old lease's button-up request could not release a newly owned button.
- The keyboard path still accepts and releases `a`; the second probe verifies
  the actual keymap while the key is down, rather than only completing calls.

Evidence: `results/pointer-owner-01` and `results/pointer-owner-02` contain
source manifests, result records and owner release records. The first and
stronger second probe sources are retained separately. These checks share a
single owner within each run, so 23 checks are not 23 independent episodes.
The scripted 60 ms observation wait is not a measured maximum release latency.
No GUI task, application-level scroll outcome, throughput or token result is
claimed from this primitive probe.

## Integration gates and known limits

The v10 shared candidate remains unchanged. This owner candidate adds core
input semantics and therefore is **not evidence of architecture-churn
convergence**. It must pass broader shared correctness checks before promotion.

Before connecting the saved OpenTTD task:

1. Bind surface and coordinate context from the same captured observation and
   define geometry-change rejection. Surface ID alone does not prevent a stale
   point hitting another control after the same window moves or its UI changes.
2. Extend whole-program validation and the backend with bounded pointer actions,
   keeping sequence/deadline/cancel authority and final cleanup. Do not bypass
   those paths with the historical direct pointer driver.
3. Handle and test surface destruction and X11 disconnection during traversal,
   admission and cleanup. Current synchronous `call` waits have no timeout;
   an owner-thread exception outside the request handler can strand a caller.
   This pre-existing fault-lifecycle limitation needs resolution before use.
4. Test nested child windows, decorations, popups/grabs and geometry changes in
   actual apps. The current probe uses simple windows. The child traversal and
   subsequent XTEST event are not an atomic transaction; race-free targeting is
   not established. Input shapes and transient overlays need more exposure.
5. Add actual shared-backend keyboard regression, then OpenTTD pointer self-use,
   fresh layout variants and interrupted-drag recovery. Horizontal wheel,
   relative camera motion, gestures and multi-device input are not implemented.

Reproduce in Linux from the repository root:

```sh
python3 research/live_control/pointer_owner_probe_v2.py \
  --out /home/taka/pointer-owner-fresh
```

Use a fresh output path. Requires the same Xvfb/Openbox/Python Xlib environment
as the existing live-control experiments. This probe is not an entry point for
operating arbitrary applications and does not replace `interactive_v10.py`.
