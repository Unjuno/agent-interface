# Receive action records and the referenced image in one model-visible result

The actual assistant run combined_image_self_use-01 used unchanged runtime v28,
socket v12, prepared caller v6 and the known prefilled browser fixture, seed
991029. After each received report, the same functions.exec invocation parsed
the result, emitted the full report, selected its validated image path, called
view_image with original detail, and emitted that image. The assistant chose the
next input only after receiving that combined result. No program steps were
selected inside the display orchestration.

Initial 001.png showed the blank browser. Navigation returned sequence 10 with
the explicit image reference 006.png, showing old-draft-42. The assistant then
used Ctrl+A, t991029, Return. Independent evaluation confirmed exactly that
submitted value. Two programs, verified release, request lineage, full retained
record prefix and all 13 reconstructed frames pass. Direct final evaluation
skipped the optional drain. Three socket exchanges occurred before cleanup, and
the server exited successfully.

The final reference 013.png still shows the form with the entered value: capture
preceded the independent evaluation. Displaying an image alongside a successful
result does not make that image a post-effect confirmation. Image capture time
and evaluation time retain their separate meanings.

## Observed timing and limits

| Measured interval | Separate form-image call | Combined report and image |
|---|---:|---:|
| Form client flush to next client main | 22003.308 ms | 17475.172 ms |
| First capture to final client flush | 72672.036 ms | 55216.132 ms |
| Navigate main to client flush | 992.360 ms | 1072.975 ms |
| Submit main to client flush | 458.674 ms | 469.575 ms |

The separate condition is endpoints-browser-self-use-01. In this sequential pair,
the form boundary is 4528.136 ms shorter, while both local caller durations are
slightly longer. These are descriptive differences, not an isolated causal
speedup. There is one run per condition, no counterbalancing, different background
timing and conversation context, and different model-visible text: this run
emits the full report, whereas the earlier run emitted selected report fields.
The full record trace is retained in both. Actual model tokens/limits and receipt
timestamps are unavailable. Each duration is computed inside its own verified
clock domain; absolute timestamps from the different runs are not subtracted.

The structural result is narrower and reliable: no separate model/tool turn was
needed to display the form image. The underlying exec and view_image tool calls
still both occurred. This is an orchestration change, not faster native GUI input
or a change to the shared runtime protocol. The residual 17.5-second outer boundary
remains far from human live tempo.

## Reusable orchestration pattern

Within functions.exec, await the authorized command that invokes v6, then parse
its complete JSON output and emit it before requesting the referenced image.
Use a sufficiently large command output budget for the full response; truncated
JSON must not be repaired by guessing. A running command/session must be resumed,
not repeated. Image display failure must retain the action report and never cause
input replay. For this Windows-hosted WSL workspace the path mapping is explicit:

```javascript
// commandResult is the completed exec_command result, not a new action request.
if (commandResult.session_id || commandResult.exit_code !== 0) {
  text(commandResult); // inspect or resume; do not automatically reissue input
} else {
  const report = JSON.parse(commandResult.output);
  text(report); // preserve all records, including intervening events
  if (report.image?.status === 'image') {
    const path = report.image.path;
    const allowedRoot = '/mnt/c/Users/junny/Documents/New project/agent-interface/research/live_control/results/combined-image-self-use-01/';
    if (!path.startsWith(allowedRoot)) throw Error('Unexpected image root');
    try {
      const result = await tools.view_image({path: 'C:/' + path.slice(7), detail: 'original'});
      image(result.image_url);
    } catch (error) {
      text({image_display_error: String(error), action_replay: 'not requested'});
    }
  }
}
```

The trusted caller's receipt_image helper already resolves the path and verifies
run containment. The host mapping is deliberately scoped to this local mount;
it is not a generic cross-OS path validator. Runtime files can change between
validation and display; this is not an atomic image attestation. The original
detail setting avoids the known resized-preview rendering problem.

Use this combined display pattern for further self-use, while keeping the runtime
candidate unpromoted. Next prioritize larger tasks or new recovery cases with
explicit visual decisions, rather than repeating this known form to chase a
smaller single-run number. Evidence: audit_combined_image_self_use.py,
results/combined-image-self-use-01, results/combined-image-self-use-audit.json.
