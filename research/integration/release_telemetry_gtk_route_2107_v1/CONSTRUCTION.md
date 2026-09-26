# Construction chronology (not formal evidence)

Allocation preparation for `issue2107-gtk-release-decision-formal-01-20260926`.

1. Initial host test command `python -m unittest
   research.integration.release_telemetry_gtk_route_2107_v1.test_construction`
   stopped before tests because the new test module imported `policy` as a
   top-level module while unittest loaded it by package path. No test method ran
   and no GUI/container/formal allocation ran. The test now adds its own
   directory to `sys.path`; the command is corrected to discovery mode.
2. The accompanying host `py_compile` attempt passed a literal `*.py` path
   through PowerShell, which Python rejected with `Errno 22`. This was a command
   invocation error, not a source compilation result. A PowerShell file loop is
   used for the next construction check.
3. Cached image preflight succeeded with Docker Desktop, `--pull=never`,
   `--network none`, read-only root and `/tmp` tmpfs. It reported Python 3.13.5,
   PyGObject 3.50.0, GTK 3.24, Xlib import success, and `/usr/bin/Xvfb` plus
   `/usr/bin/xwd`. No project experiment ran in this preflight.
4. Docker construction 01 completed four fixture sessions, but its separate
   raw-only audit returned `AUDIT_FAIL`. The retained cases exposed three
   issues: (a) the window was decorated and the actual XWD geometry was 400×200,
   contradicting the frozen 400×180 parser contract; (b) event-log/effect-file
   timestamps proved the GTK state variable changed before release, but the
   captured pixels remained PENDING, so task-effect visibility had not been
   established; and (c) the no-effect retry path rewrote the first successful
   effect timestamp on an idempotent duplicate. No formal allocation or
   source-freeze commit existed. The implementation now uses an undecorated
   fixture, waits for and retains an XWD independently classified DONE image
   before the effect-before-release intervention, and preserves the first
   effect oracle while logging duplicate key effects separately.
5. The failed construction output and its exact independent `AUDIT.json` remain
   under `evidence/construction01/` and
   `evidence/construction-audit01/`. They are not deleted, overwritten, or
   reclassified as a PASS.
6. Docker construction 02 again stopped in its first effect-before-release case.
   The GTK key handler and private effect oracle changed to DONE, but all 41
   retained XWDs of the top-level XID contained one uniform background pixel;
   therefore no independent visible DONE observation was obtained and the
   release was not issued. The held F8 also auto-repeated while the bounded
   pixel gate polled, producing duplicate key-press events; the first effect
   timestamp remains preserved. This revealed that top-level `xwd -id` omits
   the GTK drawing child and that the isolated X server had repeat enabled.
   Construction 03 now gives the drawing area its own native X11 window, captures
   that exact 400×180 child XID, and disables autorepeat only on the disposable
   Xvfb server. The complete STOP bundle remains at
   `evidence/construction02/formal01/`; no formal allocation was run.
7. The first host-side standard-library audit attempt for construction 02
   returned `AUDIT_FAIL` because it required exactly 41 GTK key-press rows and
   40 duplicates, while the raw log contains 36 presses, 34 ignored duplicate
   effects, one state change, and no GTK key-release event. The evidence already
   establishes the needed bounded STOP, but that exact-count audit condition was
   over-specific. Its first output is retained unchanged as
   `evidence/construction-audit02/AUDIT.json`; corrected bounded audit output is
   written separately as `AUDIT-v2.json`. This is audit construction, not a new
   experiment or alteration of raw evidence.

8. Docker construction and audit work are currently paused at an external
   shared-Docker contention boundary. Several other Docker CLI processes are
   still pending: `docker system df`, `docker ps`, and two `docker image
   inspect` calls (one for `python:3.12-slim`, one for another agent's derived
   image). They are not this task's processes and are left untouched. The independent
   bounded STOP audit v2 therefore ran on host Python 3.12.10 and passed as
   `AUDIT_CONSTRUCTION_STOP_RETAINED`. That audit validates the retained Docker
   raw bytes, but it does not establish the still-unverified child-window and
   autorepeat fixes in construction 03. No formal allocation has run.

9. Local prerelease review tightened (but did not repair a treatment-arm
   confound in) the initial event-order schedule. The original already matched
   delays across receipt arms within each scenario; its `before` effect was
   immediate on F8 press while its `after` effect was delayed after F8 release.
   The revised schedule uses the same frozen 120/180/240 ms delay after F8 press
   for the before-release case and after F8 release for the after-release case,
   so event-order conditions share the nominal delay too. This was changed
   before any freeze/formal row and is not claimed as a scientific result. The
   runner records when observations/retries become available to the policy,
   and the independent audit now reconstructs the consumed inputs, wait timing,
   and retry ordering. Host tests cover the matched schedule and policy
   thresholds. This is an unallocated construction correction; it does not
   erase or reclassify earlier STOPs.

10. The retained construction-02 STOP bundle was re-audited with the current
    standard-library auditor on the host, writing a new report to
    `evidence/construction-audit03/AUDIT-v1.json`. It again returns
    `AUDIT_CONSTRUCTION_STOP_RETAINED`, errors `[]`, 41 uniform 400×200
    top-level frames, 36 key presses, zero GTK key releases, one effect-state
    change and verified X-server key-up during owner cleanup. The prior audit
    reports and raw frames were not overwritten. This still does not test
    construction 03's native drawing-child capture or disabled autorepeat.

11. Before any freeze, the formal trace audit was consolidated into the
    unit-tested `audit_decision_trace` path. A synthetic valid QUERY→WAIT→QUERY→
    CONTINUE trace now checks observation/receipt consumption order, freshness,
    requested and elapsed wait, and the controller timestamp's ±2 ms sampling
    skew. Mutation checks reject late observation consumption, a wrong query
    number, and an underslept WAIT. The first implementation's one-sided time
    comparison would have rejected a correctly sampled elapsed value because
    the runner samples elapsed immediately before `at_ns`; the tolerance is now
    symmetric and regression-tested. Seven local tests pass; this is audit
    construction only, not container verification or a formal result.

12. Docker construction 03 started from the pinned Linux/amd64 image but
    STOPped in case 001 before any key action because GTK allocated the native
    DrawingArea as 400×200 while the source gate expected 400×180. Focus setup
    matched, autorepeat was disabled, and both GTK/Xvfb cleanup exited; the
    exact raw case and runner STOP remain in `evidence/construction03/run01/`.
    The fixture now requests a 400×180 DrawingArea explicitly. This STOP is not
    formal evidence and is not overwritten.

 These entries form the construction history. They are not
formal rows and are not silently relabeled as successful tests.

13. Docker constructions 04–08 retained unchanged STOP evidence. The runs verified GTK's requested 400×180 native child and Xvfb's -r autorepeat-off setting, but their PENDING/green pixel gate correctly refused release. `effect.json` recorded DONE while draw_calls_before_oracle=0; `app.stderr.log` repeatedly reports `Couldn't find foreign struct converter for 'cairo.Context'`. The pinned sha256:eb3ce9f5… image does not contain Debian packages python3-cairo or python3-gi-cairo; requiring the Cairo GI namespace alone does not install their converter. Construction 08's explicit missing-context guard changed nothing. This route is held at STOP pending a reproducible offline GTK/Cairo dependency solution or a revised image freeze; no formal block has been allocated.

14. Attempted a local derived-image construction by adding Debian `python3-cairo` and `python3-gi-cairo` to the existing GTK image recipe. The original image's matching cached build remained a false positive: `python3` still could not import `cairo`. A clean BuildKit package-install step then remained stalled downloading the Debian package index; concurrent duplicate builds were cancelled after process inspection. The previous pinned image and all experiment STOP bundles are unchanged. This infrastructure attempt did not produce or validate a derived image and must not be interpreted as a pass.
15. Construction 09 attempted a Cairo-free GdkPixbuf effect widget but STOPped at fixture startup due to a line-joining syntax error; its exact runner STOP and stderr remain in `evidence/construction09/run01/`. After correcting the source, construction 10 completed all four smoke conditions using the existing pinned `linux/amd64` image, private Xvfb `-r`, and red/green 400×180 GdkPixbuf replacement. Its separate Docker auditor (`evidence/construction-audit10/AUDIT.json`) returned `CONSTRUCTION_AUDIT_PASS`, `errors: []`; raw XWD/effect/event/cleanup evidence is retained under `evidence/construction10/run01/`. This is construction evidence only, not a formal or decision-value result. The preregistration now describes the actual frozen fixture route. Cairo-dependent construction failures and the unsuccessful derived-image APT attempt remain unmodified.