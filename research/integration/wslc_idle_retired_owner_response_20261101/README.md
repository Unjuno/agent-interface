# Idle response buffered across owner retirement

This packet supports draft [PR #10094](https://github.com/Unjuno/agent-interface/pull/10094);
it does not install the candidate in runtime. The predecessor is
`3e9d295e3ff1602bec844ea3610c0ec5a9cfee44`, the candidate is
`e6ed07edad270cc4631518bf3b53124e4ada28b6`, and main at freeze was
`0e5f70d91a6228ce0e54e215c16587391ce3f9e3`.

A simulated parent-side probe held an idle reply, retired the simulated child,
then released the reply. The predecessor accepted the old observation and
restored `state=open`. A regression test failed before the candidate and
passed after it; 94 selected WSLc tests passed under normal and optimized
Python. The candidate serializes idle response publication with quarantine at
retirement. The simulated test does not demonstrate GUI behavior or release.

Two separately frozen WSLc/Xvfb trials used real spawned owners and one
synthetic target. The parent paused after receiving the complete idle reply,
retired the exact child, then delivered the buffered reply. In the predecessor
arm the reply was accepted and state returned to `open` despite the dead child;
in the candidate arm it was rejected and state stayed failed, review-required
and quarantined. Each arm then used a **new** owner to type `a`, independently
observe the target's key release, and verify neutral input. Old-owner cleanup
was `UNKNOWN` in both arms. No old input was held when the child was retired.
The parent pause is injected; one run per arm does not establish general
recovery, physical release bounds, other fault classes, or MAP01 behavior.

`raw.zip` contains frozen source, conditions, reports, synthetic target events
and test output. `archive-manifest.json` hashes the entries. Run `python
audit.py` to verify the archive and re-run the saved report auditor. Host-local
`private-command.json`, Python bytecode and the Windows red-test traceback
containing a local path are excluded; originals remain local. The audit checks
stored evidence consistency and cannot prove absent unrecorded events.
