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

If the outcome is early saved-effect evidence, the adapter now composes the
existing `drain_final` policy: one command-free request for an already-available
independent evaluation, zero server wait, and a 250-ms transport deadline.
No loop or input retry occurs. Pending/lost reads retain early evidence and a
continuation; mismatched identities require reconciliation. Exact final-read
requests/replies and the full drain interpretation are retained. An evaluated
result can therefore arrive with the original action response without another
model/tool turn. If evaluation arrives too late, a later command-free read is
still required. Early effects are never promoted to task success by themselves.

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

## Return the receipt and image together

Pass `--review` to `agent_exchange.py` to compose the action attempt and its
review in one CLI invocation. The raw report is persisted first. Review failure
returns that action result plus `review_error`; it never repeats input. The CLI
exit status continues to describe the action adapter status, not rendering or
task success. Forward the optional image block as described below.

After `run` has persisted its report, `agent_review.review(report_path,
run_directory)` returns the receipt view plus the exact referenced PNG bytes
as an image content block. It can run immediately after the action in the same
Python process. For an existing report:

```sh
python research/live_control/agent_review.py --report results-local/edit-1/report.json --run-directory results-local/session
```

Forward the `image` block to the host image channel, not to text. For this
tool host, after awaiting the completed CLI command:

```javascript
if (commandResult.session_id || commandResult.exit_code !== 0) {
  text(commandResult); // resume the existing session; do not repeat the action
} else {
  const review = JSON.parse(commandResult.output);
  const frame = review.image;
  delete review.image;
  text(review);
  if (frame) image(frame);
}
```

The output budget must fit the complete JSON plus base64 image. Truncation must
not be repaired by guessing or replaying input: repeat only the read-only review
with an adequate output budget, or use the existing file-image path. Base64 adds
transport bytes; there is no token-saving claim. This path removes host path
mapping and a separate image-read tool call. The host still performs image
rendering. The helper does not decode PNG pixels; it checks the signature and
hash of the exact encoded bytes passed to the renderer.

Newest-reference conflicts, missing images or changed saved image identities
return `image_status="needs_review"` while retaining the receipt. There is no
fallback to the pre-action source image. Full intermediate history remains in
the original report. The image remains a historical capture and may precede
task evaluation; displaying them together does not prove a post-effect capture.
