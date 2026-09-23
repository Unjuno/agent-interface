# Fixed-byte snapshot index density (c5d2)

Research-only measurement of the unchanged prior eager snapshot. 9 formal cases,
retained raw allocation traces and exact bytes; no runtime or default change.
Read REPORT_JA.md and prospective LOCAL PLAN.md/FREEZE.json. GitHub publication
is still unavailable in this session; this directory is staged, not remote.

Restore the complete evidence first:

    python -B restore.py --out /tmp/c5d2-fresh-audit
    python -B /tmp/c5d2-fresh-audit/audit.py /tmp/c5d2-fresh-audit
    cd /tmp/c5d2-fresh-audit
    python -B -m unittest -v test_audit

Do not rerun supervise.py/run.py with the consumed allocation. The old demand-
index construction STOP is provided separately and must not become a duplicate
formal task competing with #4068. Same-author raw audit is not external approval.
