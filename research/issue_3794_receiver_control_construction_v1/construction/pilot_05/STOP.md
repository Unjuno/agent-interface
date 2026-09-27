# Construction command pilot 05 — STOP

The container image has `python3` as its ENTRYPOINT. The exploratory Docker invocation incorrectly supplied an extra `python3` argument, so Python attempted to open `/repo/python3` and exited 2 before loading the runner. No Xvfb, receiver, candidate or formal allocation ran. The invocation error is retained here. Corrected frozen commands omit the redundant executable argument; this STOP does not count as a formal runner invocation.
