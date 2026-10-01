# Result: immutable failed audit (T0)

Allocation `MAP01-OWNER-OCCURRENCE-BINDING-59-T0-20261001-01` was run once on
Windows CPython 3.12.10 against the unchanged `InputOwner` source pinned at
`288d0498d11cf16657e523a04616bf4f49cd94f4` (blob `c40db07e596b31557590cec5e90f6ab651573476`).
The in-process fake transport received `KeyPress, KeyRelease, KeyPress,
KeyRelease`; two admissions and two release brackets were recorded, and the
single terminal close sample reported no keys held. The candidate ran once, with
zero retries. Docker Engine and a real X server were not used.

The independent audit ran once and returned `FAIL_AUDIT`. The auditor
incorrectly required both release records to carry key name `W`. The source
intentionally records the explicit-up key as `W` but records owner cleanup by
keycode with `key: null`. Its source establishes both rows have keycode 25, the
same owner/intent, and no occurrence ID; the raw record confirms this. Thus the
failed audit is an oracle/validator defect, not evidence against the source
boundary. It is retained unchanged. The corrected criterion is staged only in
the planning notes; this allocation must not be rerun or have its raw/audit
outputs rewritten. A separate successor allocation is required to validate
that criterion.

Scope is strictly Python owner record behavior under a fake Xlib transport.
Nothing here establishes real X11 sampling, physical occupancy, application
delivery, input effectiveness, game performance, or production readiness.
