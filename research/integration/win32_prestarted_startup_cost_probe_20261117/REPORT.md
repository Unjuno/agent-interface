# Win32 producer startup-cost probe (2026-11-17)

## Result

Five paired, alternating trials on Windows 10 build 26300 with CPython 3.11.9
measured the ordinary producer setup plus `Process.start()` at a median **17.962
ms** (range 5.917–20.667 ms). The prestarted factory's initialization through
its child-ready receipt took a median **176.396 ms** (range 175.187–181.915 ms).
That is 9.82x the ordinary measured startup interval, or 158.435 ms more at
the median. These are descriptive measurements from one host and five trials.

Every trial used the real `NativeWin32StandardProducerFactory`; both used an
inert fixture HWND and one operation descriptor. No authorization gate was
opened, no input was sent, and all ten child processes were retired. Per-trial
timings, order, readiness and cleanup receipts are in
[`raw-results.json`](raw-results.json); conditions were written before the run
in [`PREREGISTRATION.md`](PREREGISTRATION.md). Raw SHA-256:
`f269844419a20b617e23d7f17729787e85c83ba241b1879c660607fb45e85df1`.

## Interpretation

On this host the candidate does not remove process creation cost. It shifts a
longer readiness interval into server initialization and adds a ready handshake
and fixed-size receipt allocation. The probe does not include target binding,
model reasoning, task execution, recovery, server startup outside this factory,
or end-to-end token/latency accounting. It is not a full efficiency comparison,
live-control result, reliability estimate, or explanation of R273's 90.047 s
`Process.start()` observation. R273's frozen host/run and this probe's host/run
are not interchangeable. R273's next action-specific prestart hypothesis needs
a reproduction of its startup tail before this candidate can be credited with
efficiency benefit.

## Verification

- Probe: 10/10 measurements completed; 10/10 children retired; 0 gates opened.
- `python -m py_compile .../run_probe.py`: passed.
- `git diff --check`: passed.
- Initial full-suite runs exposed fixed-window test instability: normal mode had
  119/123 pass, 2 failures and 2 errors; `-O` had 121/123 pass and 2 errors.
  The deadline fixture expected automatic completion recovery with only 500 ms
  before its 1.8 s caller-grace expired, while another test polled a deliberately
  delayed 7 s recovery result for only 5 s. The initial `-O` log is retained in
  [`test-opt.log`](test-opt.log).
- The deadline fixture now completes 200 ms after its 3 s lease, leaving 1.6 s
  for automatic recovery before fallback. The delayed-result poll now derives
  its deadline from the 7 s injected delay plus a 3 s startup/scheduling margin.
  Neither change alters runtime recovery semantics or expected custody/action
  classifications.
- After those test-fixture corrections, all 123 tests passed normally in
  152.549 s and under `-O` in 146.562 s. Full output is retained in
  [`test-normal-final2.log`](test-normal-final2.log) and
  [`test-opt-final2.log`](test-opt-final2.log). The two corrected tests also
  passed together under both modes. No production runtime source was changed by
  the probe or the test stabilization.

## Decision

Do not claim an efficiency win from prestarting on this evidence. The candidate
may still protect a short action lease from variable process-start tails, but
the hypothesized R273 tail was not reproduced here, and the measured readiness
cost is paid before task admission. Keep #57 open and compare full lifecycle
costs on a host that reproduces the R273 startup condition before promotion.
