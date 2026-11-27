# R93-A01 result — provider usage path

## Outcome

`PASS_PROVIDER_USAGE_SCOPED`. The corrected worker command disabled every configured MCP; the worker's live status gate confirmed all servers were disabled before generation. Exactly one read-only model turn started and completed, with one eligible structured answer. No retry occurred.

The answer identified `Sheet1`, selected cell `A1`, blank cells, and the preregistered order `A1=731`, `A2=864`, then Save. All six plan gates passed. This is image-plan correctness only; the plan was not executed. There were zero MCP calls, desktop inputs, or Calc task effects.

## Usage and protocol custody

App Server reported one-turn usage of 11,938 input tokens, 76 output tokens, 0 reasoning-output tokens, 0 cached-input tokens, and 0 cache-write tokens (12,014 total). The terminal usage object exactly matched the newest retained `thread/tokenUsage/updated` event. Journal SHA-256: `4220110239cfb60d8b1d5e72881c245f53a40b23438d612e6ce56f024c549593`.

Worker elapsed time was 5.297 seconds for this single end-to-end App Server worker invocation. It is a single exploratory observation; there is no matched baseline, no integrated tool/action latency, and no speedup conclusion. This validates Codex App Server usage reporting and journal custody, not upstream provider wire accounting or hidden provider retries.

## Evidence

The preregistration and source hashes are in this directory. The `r93-a01/` raw protocol, request/response spool, copied input image, worker result, and audit are retained locally and indexed by `RESULTS-SHA256.json`. Raw protocol includes local thread/session metadata and remains local rather than being published in the source commit.

## Next useful integration step

Join this one-turn planner receipt to the existing public-MCP caller and a fresh isolated Calc run, preserving input-release/effect verification and accounting both model usage and tool/task effects. Do not reuse this consumed model attempt.
