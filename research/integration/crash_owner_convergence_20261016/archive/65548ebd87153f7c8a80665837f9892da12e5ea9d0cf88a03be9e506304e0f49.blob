# Session-parent SIGKILL with detached X input owner — Xvfb A05

## Question and decision

**Decision: `PASS_METHOD_SCOPED`.** In one isolated Xvfb arm, a session process spawned a detached owner service, acquired a held `a` key through its Unix-socket RPC, and was then SIGKILLed. The owner observed socket EOF after the kill request, emitted KeyRelease, verified its X-server keymap was up, wrote and fsynced a recovery receipt, and exited normally. A separate X connection independently observed KeyRelease and keymap-up. The owner had been reparented away from the killed session and the supervisor reaped it with exit code 0.

This advances A04 from killing only an Executor child to killing the session process that started the owner service. It supports the detached owner/service topology as a recovery building block. It is not production integration: the probe uses a minimal XTest RPC rather than the MAP01 backend protocol, and the supervisor remains alive.

## Frozen test and observed result

The single scored run is `results/A01/RAW.json`. Key-down was independently observed before the kill. SIGKILL was requested at 132,838,184,732 ns; owner RPC EOF arrived at 132,838,503,824 ns; owner release began at 132,838,512,620 ns; its XTest sync and owner keymap-up verification completed at 132,838,716,761 ns. The independent connection observed KeyRelease at 132,839,371,505 ns and confirmed keymap-up. The session returned `-9`; the owner returned `0` without forced termination; Xvfb returned `0`.

The controller's `Popen.wait()` observation timestamp was later than the owner's release. This is scheduler observation latency, not a reversed causal sequence: the session's socket descriptor was the only client holding the owner RPC connection, so EOF after the kill request is the release trigger. The frozen gate therefore checks kill request < owner EOF < release, and separately requires the session's `-9` exit status. It does not treat the parent's later wait-return timestamp as the exact kernel death instant.

An initial setup attempt stopped before the registered kill because the harness serialized a python-xlib event through a nonexistent `event` attribute. The exact failure is retained in `RUNNER/attempt-01-setup-failure.txt`; the event projection was fixed and regression-tested before the one scored A01 run. The setup attempt is excluded from the scientific decision.

## Scope limits and next step

The harness uses one key, one Unix stream, one local Xvfb display, and one supervisor that becomes a Linux child subreaper. It does not establish production lease/focus semantics, multiple-key or mouse release, malformed/duplicate RPC handling, owner-service death, controller/supervisor death, display reset, session v12/V15 wiring, or gameplay/task effect. Do not use this result to admit a MAP01 live allocation.

The next discriminating test should run the real V12 and V15 session backend through a versioned narrow RPC adapter, kill the session during held input, and require the same independent release proof before another session can attach. Owner-supervisor failure and display teardown remain separate gates.

## Validation

`wsl python3 .../test_audit.py` — five unittest gates passed, including a guard against the Xlib event serialization defect. `wsl python3 .../audit_raw.py .../RAW.json` — `PASS_METHOD_SCOPED`. Python byte-compilation passed. The source-topology audit is separately recorded in `v39_crash_recovery_integration_audit_20261012/`.
