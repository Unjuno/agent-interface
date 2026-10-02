# Issue #59: owner-integrated focus/autorepeat probe

This additive probe tests one narrow mechanism: after a held key is admitted to
window A by the byte-identical current `InputOwner` v10, does that owner observe
focus moving to B, release the key, and verify the X server keymap before B
receives a repeat press? It is not a MAP01, gameplay, planner, or product claim.

## Current state

**FORMAL RUN COMPLETE — scoped pass recorded in `formal_01_20261002/RESULTS.md`.**
Formal candidate/auditor/retry counts: **1/1/0**. The frozen main is
a5756d9b31231a4d64268610236622ac44c36f1f; the three pinned owner-source Git
blobs recorded in raw evidence still match the latest main check
007503a7b461848539dda5ba5a795cbfdc13b9db.

Draft PR #6387 now records the formal result. Earlier static review found that
the auditor accepted missing/null owner_release.verified. The additive correction
requires the exact boolean true and adds missing/null negative controls. The
one-shot candidate exited 0 and the independent auditor returned
`PASS_OWNER_FOCUS_RELEASE_SCOPED`.

The construction regression suite passed **28/28 inside WSLc** on 2026-10-02.
It includes both process-boundary controls and rejects missing/null release
verification. A dedicated image was built from the pinned Python image; its
identity and full build log are retained in BUILD.md and IMAGE_BUILD.log.
The host is Arch Linux under WSL2 (kernel 6.18.40.1-microsoft-standard-WSL2),
not Ubuntu or WSL 3. At the lane check, WSLc had zero running containers and the
WSL process snapshot showed only a resident Ollama server; no Xvfb or GUI worker
was present. The user's instruction to run in a WSL container authorizes this
single bounded CPU/Xvfb allocation. No GPU allocation is used or claimed.

WSLc warned that cgroup/swap memory-limit enforcement is unavailable. The
requested 512M is recorded as a request only. Candidate and auditor used the
pinned local image with pull disabled and network disabled.

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
- The candidate process writes `raw.json` only. It does not import or invoke
  `audit.py`, and it does not produce a classification. After a successful
  candidate exit and raw-file preservation, invoke `audit.py` in a separate
  process/container against only that immutable raw file. Retain distinct exit,
  stdout and stderr records for both processes.

## Runtime and commands

Build the dedicated image from the frozen Dockerfile using WSLc, then verify
the image ID and dependency versions before freezing. Candidate and auditor run
in separate, disposable WSLc containers with network disabled, read-only source,
and separate output files. The exact formal commands are recorded in
formal_01_20261002/COMMANDS.txt; candidate output is written once to a unique
path and is never overwritten.

## H/T/D/C/U

- **H:** with confirmed autorepeat and one owner-admitted held key, observed
  focus loss causes verified owner key release before B receives another
  matching `KeyPress`.
- **T:** one candidate process and one separate raw-only auditor process; positive
  control has at least two presses; one A-to-B transfer; bounded event-pump
  interval; no retries or inferred repetitions.
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

Even a pass is only a narrow Xvfb mechanism result and does not satisfy Issue
#59's live threat-exposure/MAP01 exit condition.

The event-pump review findings are addressed: B's KeyPress/KeyRelease selection
is established on the same X connection that reads B events before focus
transfer; shutdown performs XSync and a final drain; pump exceptions, missing
subscription, missing fence, or ambiguous post-release matching presses force
HOLD. These conditions have mutation and fake-reader tests. The frozen-main
construction suite passed 28/28 inside WSLc before the candidate.

A matching B KeyPress dequeued at or after the owner release timestamp is ambiguous under scheduler delay and forces HOLD; it cannot be counted as evidence for PASS. The final 100ms settling interval plus XSync and final drain preserves late queued events for that conservative decision.

## Formal outcome

The repeat positive control observed four KeyPress events and verified release.
After the observed A-to-B focus transfer, InputOwner v10 emitted a verified
focus-change release with an empty keymap before any matching B KeyPress. The
same-connection B reader completed its XSync final drain; the independent
auditor classified the trial `PASS_OWNER_FOCUS_RELEASE_SCOPED` with zero
pre-release matching B presses. Full timings, process records, and SHA256 hashes
are in `formal_01_20261002/RESULTS.md` and `RESULTS_SHA256SUMS.txt`.

This is a single private Xvfb/XTEST mechanism result. No GPU was used because
this event-order fixture is not GPU-compute-bound.
