# Observed input focus as an experimental input guard

`session_v6.py` samples X11 input focus before image capture and after context
collection. When those samples agree, their window ID can bind a new intent.
`input_owner_v2.py` checks that ID immediately before each key-down, in addition
to expiry/cancellation. A mismatch produces `needs_decision` and no new key-down.
The input owner also samples focus while an intent is active and releases held
keys when it changes. Once detected, focus invalidation persists for that lease
even if focus returns. A new intent needs a newly established binding.

This checks actual X11 input focus, not just the active top-level window title.
It is not semantic application identity, an atomic capture/input transaction,
or a complete focus-history sensor. Focus can change between check and injection,
change away and back between polls, or reuse an XID. Two matching samples do not
prove the image/context represents a stable interval. Query failure and owner
thread health still need supervision. No hard real-time guarantee is claimed.

## Evidence

Eight fresh private-Xvfb probes (`results/focus-01`) compare the previous owner
with the candidate over two seeds, with unchanged focus and an explicit focus
transfer after observation. The destination is a visible independent X11 window
that collects KeyPress events; the original application is a real XTerm.
Arm order reverses for the second seed. The observation sequence stays current
in both arms, demonstrating why sequence equality alone misses external change.

- Both baseline transfer cases delivered the test letter to the other window.
- Both candidate transfer cases emitted no input admission and stopped with
  `needs_decision`; the destination received no KeyPress.
- All four unchanged-focus cases completed with input admission and verified
  release. This is a limited false-rejection check, not broad GUI coverage.
- All eight cases verified terminal release. Fourteen recorded frames reconstruct
  exactly and match PNG pixels. Key delivery is recorded by the probe in reports;
  raw X event objects were not archived, so that part is not independently
  reconstructible from the audit artifacts.

`test_focus_owner.py` verifies release during a held modifier, persistent lease
revocation after returning focus, and new-lease input. Its initial assertion raced
the release record: the monitor saw key-up before the owner appended verification.
The test now waits for both independently observed release and its record, with
a bounded wait. The corrected test passes. Inherited startup ResourceWarnings
remain unchanged; private test temporary directories remain after process cleanup.

Actual assistant use through `interactive_v7.py` completed XTerm seed 930201:
the assistant inspected the initial and saved screens and submitted t930201.
Independent saved-text evaluation passed; three frames audited exactly and owner
shutdown verified release. Local acceptance-to-first-image-ready was 151.1 ms,
not a matched speed comparison or remote planner timing.

## Scope and next work

Revision 7 is experimental. It preserves the original image packets and existing
operation vocabulary. Capture-time focus fields are additional event metadata;
the packet codec has not acquired semantic validity guarantees.

If the before/after samples differ, the backend currently cannot bind an intent,
including an observe-only program. A recovery observation lane independent of
input authority is therefore required before making this the default runtime.
A hold can release asynchronously while the worker keeps observing until its
next input or normal step completion; notification latency is separate. Focus
changes caused by legitimate UI actions, modal transitions, harmless animation,
stale intermediate snapshots and recovery cost need explicit evaluation.

Run from this directory in the documented Ubuntu/WSL environment:

```sh
python3 probe_focus.py --out ../../results-local/focus-new
python3 -m unittest test_focus_owner -v
python3 audit_focus.py results/focus-01
python3 audit_owner_sessions.py results/focus-assistant-01
python3 interactive_v7.py --app xterm --seed 930401 --out ../../results-local/focus-session
```

The paired cohort freezes directly measured source hashes. The interactive
session additionally hashes its inherited GUI and codec sources. These are
development probes and self-use evidence, not human-speed, token-saving or
generic wrong-target prevention claims.
