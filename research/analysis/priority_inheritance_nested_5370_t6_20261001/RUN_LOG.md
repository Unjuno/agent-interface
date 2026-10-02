# T6 run log

- Environment: Windows host, CPython 3.12.10; no container, model/provider, network, GPU, GUI, or application input.
- Docker disposition: no shared slot was explicitly assigned to this experiment. Docker Desktop was not invoked and no existing container was inspected, stopped, or changed.
- Frozen candidate: `scheduler.py`, SHA-256 `b115895a1b0ebe1ea7c8815f4360cbb05658c939947518ae02f314972cabc556`.
- Frozen oracle: `audit_raw.py`, SHA-256 `374531c536da5c01d7e02db431d937691025fd827e0767a664e0655794ef61e4`.
- Test sources: `test_scheduler.py` SHA-256 `6761a5f2e391314e777917bf380e0beef50df4aa60198348fa591602a92a0a8f`; `test_audit.py` SHA-256 `39ab6b915228fffeef6b351e13e0e7023e2a66cb81540afa1f6c1b165bdbf81cd`.
- Construction verification: `python -m py_compile scheduler.py audit_raw.py test_scheduler.py test_audit.py` — exit 0.
- Construction suite: `python -m unittest -v test_scheduler.py test_audit.py` — 9/9 pass (four candidate behavior tests; one valid-raw and four corruption/coverage controls).
- Frozen candidate invocation: `python scheduler.py --output results/formal-01/raw.json` — one invocation, exit 0, four rows. Raw SHA-256 `39adda08f06e1a15b3e74ac05660c49d2112e806635db63cbe90d9fea65208b2`.
- Frozen raw-only audit: `python audit_raw.py` — first invocation exit 0; `PASS_AUDIT_V1_SCOPED`, rows 4, errors `[]`.
- The raw file's filesystem write time is 2026-09-30 17:35:22 UTC. The tool did not expose a per-command timestamp for the auditor; both frozen invocations occurred in the 17:35 UTC work interval.
- Protocol deviation: a later final-check command re-ran `python -m unittest -v test_scheduler.py test_audit.py` after the formal audit. Its `test_accepts_exact_four_row_replay` evaluated the frozen raw with the audit function. The same final-check command also unintentionally ran `python audit_raw.py` again. Both returned no errors on the unchanged raw SHA; no candidate rerun or raw modification occurred. The one-audit preregistration is violated, so terminal disposition is `STOP_PROTOCOL_DEVIATION`, not PASS. All three evaluations are in `results/formal-01/AUDIT_RECEIPTS.md`.
