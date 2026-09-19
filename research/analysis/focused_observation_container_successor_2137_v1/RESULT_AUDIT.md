# Formal result audit

Run 35444300481 executed the validator once in python:3.12-slim and independently audited the retained 256 raw rows from a separate container invocation. All 256 rows agreed with the independent oracle; accepted=8, mismatches=0, authority-positive=0. Paths were resolved relative to the audit module. Model, GUI, network, and task-input counters were zero.

Artifact 10585066487 digest: sha256:f936ed86a041f59f05a7f2559ddabfb33adf1b5d9aaa8bdb7ec6533bdbdbf74f.

This is request-validation evidence only. It does not establish model behavior, GUI correctness, automatic region discovery, latency, token impact, or cross-domain transfer. Prior #2058 and Docker HOLD #2154 remain unchanged.
