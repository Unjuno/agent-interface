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
