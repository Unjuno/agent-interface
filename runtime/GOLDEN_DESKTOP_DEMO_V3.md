# Golden desktop demo v3 candidate

V3 repairs the environment-closure failure retained by the first v2 allocation.
It does not change the six GUI tasks, adaptive acquisition policy, repair path,
independent scorer, or persistent app-server grounding adapter.

The pinned runtime now includes `openpyxl==3.1.2` and
`et-xmlfile==1.1.0`.  Doctor imports both modules before any model call and
reports their versions in `agent_interface_golden_doctor_v2`.  This closes the
specific false-positive that allowed v2 to spend its schema preflight and start
an app-server thread before the GUI process failed on import.

```bash
bash runtime/setup-golden-demo-v3.sh
bash runtime/golden-demo-v3.sh doctor
bash runtime/golden-demo-v3.sh run
```

Before rebuilding the existing venv, v3 doctor failed both new checks while all
thirteen inherited checks passed.  Rebuilding from `requirements-golden.txt`
installed the pinned pair and the same fifteen-check doctor passed.  Seven
offline tests cover the v3 doctor, retained v2 report gate, one-thread/two-turn
identity, unique call IDs, per-turn usage conversion, workspace/contract
refusal, and the minimized app-server command.

The retained v2 output remains a dependency failure and must not be retried.
Freeze a new v3 allocation before any live run.  Use seed 991030 and preserve
the retained v1 correctness, route, release, timing, and usage reference without
treating the sequential same-host observations as a population comparison.

## First frozen allocation

`golden-desktop-app-server-v3-live-01` passes all frozen gates in its only run.
The independent scorer records one exact submission for each of six tasks.  The
route is cold/reuse/reuse/repair/reuse/reuse; task 4 rejects the old layout with
zero old-target pointer admission and repairs successfully.  All 57 terminal
programs verify empty input release.

The two image-grounding calls are distinct turns on one capability-minimized
app-server thread, with zero MCP startup notifications.  Together with the
separate schema preflight there are three unique model call IDs.  Reconciled
usage is 27,892 input, 7,936 cached input, 477 output, and 132 reasoning output
tokens.  Six-task time is 37,714.870 ms, whole-command time is 52,180.750 ms,
and median input feedback is 99.562 ms.

Against the retained v1 same-seed reference, descriptive differences are
+1,361 input tokens, +3,072 cached input tokens, -3 output tokens, -3 reasoning
tokens, -9,745.218 ms over six tasks, -6,698.062 ms over the whole command, and
-1.714 ms median input feedback.  These are sequential single observations on
one host.  They do not establish a causal speedup, token saving, population
rate, general GUI reliability, human speed, or production readiness.
