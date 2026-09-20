# Issue #2704 stale Calc target receipt — formal01

This is a bounded private-fixture test of one observed stale-coordinate hazard.
It is not a retry of #2704's post-emission allocation and does not explain its
`FAIL_EFFECT_MISMATCH`.

## Frozen design

See Issue [#3866](https://github.com/Unjuno/agent-interface/issues/3866) for
the H/T/D/C/U preregistration and construction amendment. Formal schedule is
`A1, B1, B2, A2, A3, B3` across six fresh Calc/Xvfb sessions. A uses the
historical coordinate with no target receipt; B requires an app-owned UNO cell
selection and matching active window identity before any keyboard task input.
The screen point is intentionally kept fixed at `[89,200]`; if it changes to a
non-target again, B must refuse without correction or replay.

Construction probe #3862 measured `[89,200]` selecting `$Sheet1.$A$3` in the
current 1280x800 Calc fixture. It sent no text or save action. Formal01 will
retain that mapping if it reproduces. Only A controls may write into their new,
disposable workbook; each B gate arm stops before task keys when selection is
not `$Sheet1.$A$1`.

## Container

Docker Desktop Linux/amd64 image:

`issue2704-calc-readiness:formal01@sha256:41c3190256bf644c8e251bb84d615d2753fae067e347422fd6d3e74ec8d60183`

Base image digest: `c0d1b4471b2095cec5aee92d31a46e35a96a20b6cf469443c307e9670b493544`.
Formal sessions use `--pull=never --network none --read-only` and a fresh writable
evidence bind mount plus a bounded `/tmp` tmpfs. `/usr/bin/python3` is required
for Debian's matching UNO/Xlib bindings.

The independently installed versions were: LibreOffice Calc
`4:25.2.3-2+deb13u6`, `python3-uno` `4:25.2.3-2+deb13u6`, `python3-xlib`
`0.33-3`, openpyxl `3.1.5+dfsg-2`, xdotool `1:3.20160805.1-5.1`, wmctrl
`1.07+git20240228.1105759-1`, Openbox `3.6.1-12+b2`.

## Evidence boundary

`record_monitor.py` uses the X11 RECORD extension independently from the runner
to capture core Key/Button events. `audit.py` (separate container invocation)
will read event traces, saved workbooks and hashes without importing runner code.
The test does not call the production native exchange/CLI, a model/provider, or
an external API. A scoped PASS only demonstrates this selection gate on this
private fixture; it is not a production readiness or general reliability claim.

