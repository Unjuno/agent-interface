# Issue #59: owner-integrated focus/autorepeat probe

This additive probe tests one narrow mechanism: after a held key is admitted to
window A by the byte-identical current `InputOwner` v10, does that owner observe
focus moving to B, release the key, and verify the X server keymap before B
receives a repeat press? It is not a MAP01, gameplay, planner, or product claim.

## State

**NOT RUN — shared WSL/Xvfb lane occupied.** On 2026-10-02 the local Ubuntu
distribution was WSL 2 (kernel `6.18.40.1-microsoft-standard-WSL2`), not WSL 3.
It already had `/usr/bin/Xvfb`, Python 3.12, and system `python-xlib`; Docker was
not installed in the Windows shell. Concurrent native runtime workers and
another agent's `Xvfb :27000`/LibreOffice session were visible. No packages were
installed, no shared process was stopped, and this probe was not launched.

The completed work is only construction/contract validation: 18 standard-library
auditor tests pass on Windows and under WSLc's pinned Python image, the probe
imports under WSL Ubuntu, and the CLI help path works. WSLc emitted its known
no-cgroup/swap-limit warning; the accepted memory flag is not evidence of an
effective cap. This is not candidate or formal experimental evidence. In
particular, the classifier is not yet validated against a collected Xvfb result.

## Frozen candidate boundary

- One invocation; zero retries; unique output directory must not exist.
- A private Xvfb display is selected from a bounded range and the probe refuses
  if either its socket or lock path already exists.
- A positive repeat control must produce at least two `KeyPress` events and
  verify the released key is absent from the server keymap, or execution stops.
  It sets and reads back autorepeat on the disposable private Xvfb only
  (`xset r rate 100 20`, confirmed via `xset q`) and holds for 240ms so the independent control spans
  the configured 100ms initial delay.
- The owner trial sends only one `w` down to A, requests focus transfer to B,
  records the actual observed focus, waits for the owner's own `focus_changed`
  release record, then samples a finite B event-pump interval.
- Raw records retain the refrozen main SHA, exact expected Git blob IDs and
  SHA-256 values for `input_owner_v10.py`, `executor_v3.py`, and `lease.py`;
  mismatched source bytes stop before Xvfb starts. Xvfb status and private
  socket/lock cleanup are required for a passing classification.
- The classifier counts only B's matching keycode `KeyPress` received after the
  focus-change request begins and before the owner's verified release record;
  this includes events delivered while the requester awaits XSync. The owner
  connection's own focus-query timestamps
  are instrumented through a delegating display proxy; owner source bytes stay
  unchanged, but the proxy adds a small timing perturbation.
  It does not use a candidate-supplied status field.

## Commands

From PowerShell at the repository root, run the no-network construction suite in
the already-cached digest-pinned WSLc image:

```powershell
$sourcePath = (Resolve-Path .).Path
wslc run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${sourcePath}:/src:ro" --workdir /src `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B -m unittest -v research.doom.map01_focus_repeat_owner_59_t0_20261002.test_audit
```

The currently cached approved image does not contain Xvfb, `xset`, or Python
Xlib, so it is not yet a valid container for the formal probe. Do not run that
probe directly in the shared Ubuntu distribution or silently add packages to
the frozen image. A separate owner-authorized, pinned WSLc image containing
those dependencies is required; its digest, package manifest and no-network
runtime command must be preregistered before the one candidate invocation.
The candidate also requires explicit shared CPU/Xvfb lane assignment. Once both
gates are satisfied, run it once into a new output path and retain `raw.json`,
`classification.json`, `xvfb.stderr`, and `error.txt` if present. A clean stop
or hold is evidence too, but does not demonstrate that the safety behavior passed.

## H/T/D/C/U

- **H:** with confirmed autorepeat and one owner-admitted held key, observed
  focus loss causes verified owner key release before B receives another
  matching `KeyPress`.
- **T:** one invocation; positive control has at least two presses; one A-to-B
  transfer; bounded event-pump interval; no retries or inferred repetitions.
- **D:** the returned classification is reconstructed from `raw.json` by
  `audit.py`; report event receipt times and owner/keymap release records.
- **C:** private Xvfb + Python Xlib + `xset` in a pinned WSLc image; actual current
  owner v10; exact source hashes in raw data; one key and two windows only.
- **U:** one Linux/WSL host and one trial; scheduler/timing sensitive; XTEST
  autorepeat stimulus and client event delivery only. No live desktop,
  application, game, gameplay or general reliability claim.

## Outcomes

| Status | Meaning |
| --- | --- |
| `PASS_OWNER_FOCUS_RELEASE_SCOPED` | Positive control, observed focus transfer, verified empty keymap, and complete event coverage; no matching B press before owner release sync. |
| `COUNTEREXAMPLE_REPEAT_BEFORE_VERIFIED_RELEASE` | At least one matching B press arrived after observed focus transfer but before owner release sync returned. |
| `STOP_REPEAT_STIMULUS_NOT_ESTABLISHED` | The independent control did not establish at least two matching presses and a verified release. |
| `HOLD_RELEASE_NOT_VERIFIED` | Owner release/keymap record is incomplete or reports a key still down. |
| `HOLD_EVENT_COVERAGE_INCOMPLETE` | B's event pump does not span observed focus transfer through verified release completion. |
| `HOLD_RAW_RECORD_INVALID` | Schema, identity, ordering, source or timing evidence is malformed/inconsistent. |

Even a pass is only a narrow Xvfb mechanism result. Formal conclusions and the
H/T/D/C/U disposition must be added to Issue #59 after a permitted run; it does
not satisfy Issue #59's live threat-exposure/MAP01 exit condition.
