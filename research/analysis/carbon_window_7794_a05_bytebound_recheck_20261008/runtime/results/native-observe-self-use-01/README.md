# Input-free native observation continuation

2026-09-19. The primary assistant viewed the native initial PNG (`before.png`),
chose point `[130,55]` and text `observe991080`, and viewed the new observation
PNG (`after.png`) showing `saved:observe991080`. Independent fixture scoring
confirmed that exact saved text. No helper model ran; primary usage is unknown.

The continuation uses `runtime.cli_v1.observe.observe` with explicit target and
region. It does not call dispatch, focus, release or input methods. The actual
backend reader is capture-only; regression tests verify those boundaries and
connection cleanup, including error cases. The two prior program results and
their PNGs remain separate from `continuation.json` and its new observation ID.

The harness chooses the continuation after a bounded read of the independent
fixture effect file. That is an evaluation-specific trigger, not a generic
application-completion detector. This run does not implement visual target
revalidation, autonomous recovery selection or source-sequence management for
the public input API (the fixture still supplies fixed sequence/revision).

One-run measurements: input dispatch 153.585208 ms; call start to independently
scored effect 261.546626 ms; read-only continuation including image copying and
result persistence 46.094826 ms; whole harness including primary-assistant wait
24664.194192 ms. These are not matched timing comparisons or human-tempo evidence.

The stale-source control emitted zero input. Initial observation and accepted
input both verified empty release. The private fixture and Xvfb were reaped
(`cleanup.json`). `source/` retains the execution code; `SHA256.json` hashes raw
files and sources, excluding this README. Original absolute image references
resolve to results-local; copies under `native-images/` retain the same basename
and PNG hash. `after.png` is a byte-identical copy of the continuation artifact.

Use the predecessor's local dependency setup, then:

```sh
XAUTHORITY= python3 -m runtime.native_result_self_use --native-artifacts \
  --read-only-continuation --out NEW_DIRECTORY
```

View that run's initial PNG and supply its `request.json`. Earlier setup/task
failures remain unchanged in `../native-result-self-use-01/`.
