# Prepared exchange for the agent's own loop

`agent_exchange.py` composes existing v27 preparation and socket exchange. After
viewing a received image, provide its complete batch and explicit steps in one
Python call, or one JSON object on stdin:

```python
from agent_exchange import run
report = run(socket_path, received_batch, run_directory, "edit-1",
             [{"op": "text", "text": "draft"}],
             out="results-local/edit-1", boundary="terminal")
```

The CLI is `python research/live_control/agent_exchange.py --request -`.
Its JSON keys are the Python argument names (`socket_path`, `batch`,
`run_directory`, `program_id`, `steps`, `out`, and optional `lease_ms`,
`boundary`, `timeout`). `batch` is an object, not a filename. Use a new output
directory for each deliberate action. Defaults: 5-second lease and wait,
terminal boundary. `boundary="outcome"` submits the final program with
`finish_after=true`; explicit session cleanup is still required.

The adapter makes one clock request and at most one submit. It preserves the
reviewed observation/delivery reference, requires a contiguous own-clock reply
without intervening events, then uses the existing preparation logic. A clock
does not refresh the image. Any changed sequence or intervening event requires
review. This deliberately conservative candidate assumes one caller and an idle
session between decisions. It is not a continuous-game control loop.

Exact requests are persisted before transport, replies after receipt, followed
by a complete report. There is no automatic input retry. `program_attempted`
means a potential transport write, not admission or execution. On uncertainty,
inspect saved artifacts and reconcile with command-free reads. A reused output
directory is refused, but a different directory is not a session-wide replay
guard. Persistence failure can leave a partial artifact set; the CLI reports
unknown attempt state in that case.

`boundary` status and CLI exit zero do not mean task success. Inspect terminal
status, release and independent evaluation. For a smaller presentation of the
saved report, use `python -m runtime.cli_v1 receipt --report PATH`; retrieve raw
intermediate observations when they matter to the next decision. The adapter
does not infer actions, run another model, or modify frozen component sources.

Actual assistant use, including the first rejected development attempt, is
retained in [composed self-use](../../runtime/results/composed-self-use-01/README.md).
This is a research integration candidate, not native CLI/backend convergence.
