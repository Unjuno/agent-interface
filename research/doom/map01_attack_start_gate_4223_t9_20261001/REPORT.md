# T9 execution report — STOP on missing runtime executable

## Outcome

**STOP_CANDIDATE_MISSING_WMCTRL**. The native x86_64 image built and the
candidate output-mount write/readback probe passed. Xvfb/Openbox started and
the real `session_map01_v13.py` child was invoked once. It then exited 1 before
`ready` because the verified runtime source called `wmctrl -l`, but the frozen
image did not install the `wmctrl` executable:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'wmctrl'
```

No ready event, observation, PNG, command, or task-effect evidence was
produced. The independent PASS-gate auditor was correctly skipped. This is a
native image dependency gap, not a DoomGame/native-architecture failure and
not a startup PASS. T9 will not be rerun.

## Frozen run and retained evidence

- Allocation: `MAP01-ATTACK-ONSET-STARTGATE-4223-T9-20261001-01`
- Frozen source: `124451da3fde45ed0e004554474a5a28d5a8a13f`.
- Workflow run: [36797498387](https://github.com/Unjuno/agent-interface/actions/runs/36797498387)
- Actions artifact: ID `11134078845`, name
  `map01-attack-start-gate-t9-36797498387`, 85,247,135 bytes, ZIP SHA-256
  `5bb5689d6db5dc522cc2c2e5f5056df11aeb15199e543e55ff03c1b0999f7516`.
  The local ZIP matched this digest and passed `unzip -t`.
- Host: GitHub Actions Ubuntu 24.04, native Linux/x86_64; Docker Engine 28.0.4.
- Runtime artifact 10398313098, SHA-256
  `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`;
  2,592/2,592 sources and 12/12 wheels verified.
- Image: `sha256:498f8cbf14b544eb0356679fbe8e6069696fbb314d92a676b24d783dda34348c`
  (`linux/amd64`).
- Candidate output probe exit 0; mode `0o777`, container UID:GID `0:0`.
- Candidate invocation 1; candidate container exit 1; child PID 11 / exit 1;
  retry 0; independent auditor invocations 0.
- The `evidence/` directory retains the execution receipt, raw record,
  stderr/stdout and Xvfb/Openbox logs, runtime manifest, image build/inspect,
  host environment, main freeze/drift, artifact metadata and mount probe. The
  26 source hashes in RAW match the artifact manifest; child stderr SHA matches
  the preserved bytes. The independent mutation auditor did not run because
  its preregistered gate is candidate exit 0.

## Interpretation and next allocation

T8's emulated child SIGSEGV did not recur on native x86_64; T9 instead exposed
an omitted OS executable. This is consistent with an emulation-specific T8
crash but does not prove that causal attribution. It does show that the
permission repair preserved failure evidence on both environments.

The next fresh successor should add Bookworm `wmctrl` to the pinned image and
preflight the exact executable before invoking the candidate. Keep T9 and all
predecessor evidence unchanged. Scope remains startup only; no attack,
physical-edge, TASK_EFFECT, onset discrimination, recovery, map-clear, or
product conclusion follows.
