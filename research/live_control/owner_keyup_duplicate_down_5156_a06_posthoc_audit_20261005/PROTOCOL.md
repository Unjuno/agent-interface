# A04 retained candidate trace — posthoc audit A06

This is a new, read-only reconstruction of retained A04 candidate bytes. It
uses only the pre-run A04 source commit and a later commit that contains the
complete archived formal raw/logs. A05's first reader version stopped before
writing a report because its evidence snapshot omitted `audit.log`; that STOP
and its ten passing mutation tests are preserved in `inputs/A05_FIRST_ATTEMPT.json`.
A06 uses the complete evidence commit and reports a missing log as a custody
failure instead of raising an uncaught exception.

A04 remains `STOP / consumed`: its sole formal auditor invocation exited 1
before reconstruction. A06 cannot replace that invocation, change the formal
allocation disposition, or assign a scientific result. Its positive result, if
any, is only a reconstruction of the retained candidate JSON.

The saved trace question is whether `RESULT.json` contains two distinct same-
owner admissions for `A`, followed by one explicitly ambiguous release, while
preserving the fake-Xlib call order, nested owner receipt timing, false
authority fields, and neutral fake keymap. Custody checks separately report
the A04 freeze's incorrect `current_main_blobs` and absent prefreeze log entry.

Run from this directory:

```powershell
python -B audit_readonly.py
python -B -m unittest -v test_posthoc_audit.py
```

The auditor reads `inputs/` without modifying it and writes only `AUDIT.json`.
Tests use temporary copies for corruption checks. No A04 candidate, formal
auditor, container, X11 server, game, model, application, or input was invoked.

Any successful reconstruction remains fake-Xlib/direct-owner evidence only.
It provides no real X11, physical release, application consumption, MAP01,
task effect, threat response, feedback, recovery, safety, latency, or authority
result and implies no live #59 allocation.
