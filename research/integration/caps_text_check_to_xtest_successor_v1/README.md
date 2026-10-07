# Caps Lock check-to-XTEST successor (#8328)

This directory is additive research for the bounded gap left by #8255: an
external Caps Lock state change after the per-text `LockMask` sample and before
the first XTEST event. It does not modify the production backend or any prior
result.

## Status

- GitHub preregistration: [Issue #8328](https://github.com/Unjuno/agent-interface/issues/8328).
- Intake main: `798ac5ad709168ff1d27b115f10f4f96b126bb71`.
- Exact main backend source SHA-256:
  `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`.
- Exact retained #8255 candidate patch SHA-256:
  `86913be26400e2ac74b051df4bc9505a97fff60fc5dc652cab04caa4b4af9d65`.
- No source freeze and no formal case has started.
- `construction_probe.py` is excluded environment/setup code; it does not
  exercise the public dispatch or the #8255 candidate guard.

## Environment fallback

The OrbStack Docker content store fails image listing and image pulls on missing
containerd blobs. No repair, pruning or reset was attempted. A newly created
isolated Ubuntu Noble ARM64 VM is used only as a documented fallback; it has no
host folder mount or host/peer-machine network route. Results from it must be
reported as private OrbStack VM/Xvfb, never as container replication. Package
installation and source retrieval precede any formal freeze. Formal work must
avoid outbound experiment traffic and unrelated/shared VMs.

Installed construction dependencies include Xvfb 21.1.12, Python 3.12.3,
Python-Xlib 0.33, Tk 8.6.14, GCC 13.3 and libX11 development headers. A separate
TCP-disabled private Xvfb/Tk/XTEST smoke produced exact Entry value `aB2`.
The initial runner syntax error occurred before input and was corrected; neither
smoke is a formal outcome.

The first LockMask interposition probe reached XTEST input but exited before
printing its result because Python-Xlib 0.33 `Display.query_keymap()` returns a
list directly (not a reply object with `.map`). This construction failure is
preserved here; the probe now reads the returned list. The private Xvfb ended
with its wrapper, so no shared keyboard state survived.

### Construction-only first outcomes

Two new TCP-disabled Xvfb sessions completed with the corrected probe, whose
source SHA-256 is
`5f625cf4d41b942d5d9863b209ee979272ea5c00e64628d27c2aec93f473dc47`:

| Arm | Display | LockMask sample | Actor ack / post-lock | Entry value | Held keycodes |
|---|---|---|---|---|---:|
| stable | `:99` | 0 | none / 0 | `aB2` | 0 |
| interposed | `:100` | 0 | `[1,1]` / 1 | `Ab2` | 0 |

The interposition arm called `XkbLockModifiers` over a second X connection,
performed `XSync`, and independently observed LockMask=1 before the input
connection's first XTEST key event. The Entry journal shows first key `a` was
received as `A`; Shift+B was received as lowercase `b`; digit `2` was unchanged.
This establishes the fixture's deterministic ordering and Caps Lock effect only.
It did not execute the #8255 `TEXT_LOCK_GUARD`, public dispatch, a separate
controller process/IPC barrier, or any formal schedule. No source freeze or
formal case count is claimed.

## Next gates

1. Run the excluded `construction_probe.py` in two fresh private Xvfb sessions
   (stable OFF and synchronously interposed ON), retaining complete raw output.
2. Confirm actual first-character behavior and lock actor acknowledgment. If it
   does not establish the intended ordering or effect, repair only construction
   code and preserve the incident; do not count it as a formal case.
3. Build the actual public-dispatch candidate/barrier runner from exact #8255
   source; keep the controller a separate X client and use an explicit IPC
   barrier, never a timing sleep.
4. Freeze exact source closure, environment, schedule, expected outcomes, audit,
   and mutation controls in this directory and read them back from GitHub before
   the first formal case. Formal count/batches are not yet chosen or run.
