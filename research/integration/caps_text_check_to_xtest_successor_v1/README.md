# Caps Lock check-to-XTEST successor (#8328)

This directory is additive research for the bounded gap left by #8255: an
external Caps Lock state change after the per-text `LockMask` sample and before
the first XTEST event. It does not modify the production backend or any prior
result.

## Status

- GitHub preregistration: [Issue #8328](https://github.com/Unjuno/agent-interface/issues/8328).
- Intake main: `798ac5ad709168ff1d27b115f10f4f96b126bb71`; current-main refresh: `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`.
- Exact main backend source SHA-256:
  `6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`.
- Exact retained #8255 candidate patch SHA-256:
  `86913be26400e2ac74b051df4bc9505a97fff60fc5dc652cab04caa4b4af9d65`.
- `origin/main` was merged into the additive research branch; the two intervening main commits add unrelated Windows-pipe evidence and leave the X11 backend byte-identical (same SHA-256 above). The branch is now based on that current main.
- The exact 9-case schedule, 11-module public-dispatch source closure, decision rule, environment, no-rerun policy, evidence fields and 15 corruption controls are frozen in `FREEZE.json` and `SOURCE_MANIFEST.json`. The formal allocation remains not started until this exact snapshot and plan are read back from GitHub.
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
Python-Xlib 0.33, Tk 8.6.14, GCC 13.2.0 and libX11 development headers. A separate
TCP-disabled private Xvfb/Tk/XTEST smoke produced exact Entry value `aB2`.
Xvfb writes a fixed nonfatal XKB keysym warning block on stderr in this image.
The exact bytes are retained in `XVFB_EXPECTED_STDERR.txt`; preflight and each
case accept only one or two exact concatenated copies. Any other bytes or count
stops the run. A preallocation start emitted two copies, so the amended freeze
records that observed multiplicity without weakening byte identity.
The initial runner syntax error occurred before input and was corrected; neither
smoke is a formal outcome.

Before formal allocation, the original frozen commit `f393aed694248db712ec4e3393b80504d6bc0ce5`
produced two additional readiness STOPs: a preflight stderr multiplicity mismatch
and an excluded construction attempt where Xvfb's `-displayfd` pipe failed before
public dispatch. Both raw records are retained under `preallocation_stop_01/`
and `preallocation_stop_02/`. No formal case began and no allocation was
consumed. The amended runner selects an already-free explicit display from
`:99`–`:109`, checks for its socket, and keeps the exact warning bytes/count gate.

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

## Formal allocation freeze and current-main overlap review

The issue-level construction outcome above is retained unchanged. Open PR #8308 is a parallel held-key repair against the same backend file; the latest GitHub metadata marks it ready for review at head `dae92e12097907e860f68d6ee22a10cb23ace442`, and it is not integrated into main. This study's fixed `aB2` program holds no keys/modifiers; it freezes the #8255 guard patch and main backend source from current main `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`, and does not evaluate #8308 semantics. If the production backend source changes before the allocation, the run script must stop at its SHA gate; no silent source substitution is permitted.

`FREEZE.json` preregisters three interleaved fresh-Xvfb blocks (CURRENT, guard-stable, guard-interposed), nine total cases, exact order `C01,G01,I01,C02,G02,I02,C03,G03,I03`, fixed payload `aB2`, and no replacement/rerun or post-outcome tuning. `SOURCE_MANIFEST.json` pins the full imported runtime closure and executable inputs. `run_formal_once.sh` enters a fresh network namespace with no non-loopback interface or route; `run_formal.py` verifies the frozen commit and hashes, captures Xvfb/app/actor identities and exits, and stops at the first unexpected or ambiguous case. `audit_formal.py` checks event/value, dispatch, actor ACK-before-first-KeyPress, LockMask/keymap cleanup, process/Xvfb identities, imported-source closure, and runs 15 effective corruption controls. A formal run is not authorized until the frozen commit and file content have been read back from GitHub and the VM has that exact checkout.

The first host-only attempt to run X11 construction tests on macOS stopped before launching a case because the host has neither Python-Xlib nor `xvfb-run`; the three pure raw-auditor synthetic tests passed. This host STOP is not a scientific outcome. The dedicated VM has the X11 dependencies installed and will be used for formal cases if its frozen source can be refreshed without weakening isolation.

## Next gates

1. Commit/push this freeze and construction auditor tests; read the exact commit,
   `FREEZE.json`, and runner/auditor files back from GitHub before allocation.
2. Refresh the private VM to that immutable study snapshot; confirm exact
   source, dependency versions, and clean run root before entering the isolated
   network namespace for formal execution.
3. Execute the nine frozen cases once in order. Preserve a partial run and STOP
   on the first unexpected or ambiguous outcome; never replace or rerun a case.
4. Run the raw-only auditor and all 15 corruption controls, then publish exact
   hashes and scoped PASS/FAIL/STOP to this Issue and an additive result report.

## Public-dispatch construction gate

At branch commit `d40dd8a3e`, the excluded test
`python3 -B test_public_dispatch_probe.py` passed one current-main arm, one
stable #8255-guard arm and one guard/interposition arm, each in a fresh
TCP-disabled Xvfb. The current and stable-guard Entry values were `aB2`; the
interposed guard value was `Ab2`, while the runtime dispatch still reported
`completed`. The explicit fixture-only hook is applied only to a copied runtime
tree after the exact #8255 candidate patch; it blocks after saving the
LockMask=0 sample and before `key_chord` can issue the first XTEST event.

The actor is a separate process and X client. It received `LOCK_ON:0`, sampled
LockMask=0, synchronously called `XkbLockModifiers` plus `XSync`, observed
LockMask=1, then returned its ACK. In the retained fresh construction run, ACK
time was `21133200546299 ns`; the Tk Entry's first KeyPress (`A`, keycode 38)
was `21133201423305 ns`, 877,006 ns later. The resulting value was `Ab2`; final
LockMask remained 1, all 32 XQueryKeymap bytes were zero, all three dispatches
and app processes exited 0, and the actor exited 0 with empty stderr. This is a
finite construction counterexample for the candidate guard in this VM/Xvfb
setup, not a formal research allocation, natural failure-rate estimate, or
production result.

`CONSTRUCTION_RESULTS.json` retains each arm's complete runner record and
program: source/module hashes, process IDs/argv/exits, dispatch response,
independent X-server before/after snapshots, app event/value journal, actor
request/ACK, and errors. Its local raw-record audit confirmed 11 imported
runtime modules; every non-backend imported module hash is identical across
the three arms, and the two guard arms use the same candidate backend hash.
The main backend SHA-256 remains
`6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db`.
The candidate guard source and fixture hook are research-only copies. No
production runtime file is modified.

Construction-only incidents retained in this branch: (1) an initial Python
smoke had a shell quoting syntax error before input; (2) the first direct
interposition probe sent input but failed at `.map` because Python-Xlib 0.33
returns `query_keymap()` as a list; (3) the first barrier patch had malformed
hunk counts and failed to apply before any candidate dispatch. Each failure was
corrected before the passing end-to-end construction test; none is a formal
scientific FAIL. `test_lock_actor.py` and `test_public_dispatch_probe.py`
exercise only setup/construction; they are not the formal allocation.
