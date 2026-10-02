# MAP01 coast-wait health trajectory audit v1

## H / T / D / C / U

- **H:** An input-free coast envelope reused while a model call is pending can overlap observable health loss; if so, a renewed old coast is not evidence of a fresh threat response.
- **T:** Read the retained v38/v39 reports and raw runtime event streams. For each model-wait interval, bind the accepted/terminal cover programs, require every overlapping cover step to be `coast` (no motor hold), then order typed health observations by capture time and report first observed decline and total observed decline from the source signal.
- **D:** `PASS_SCOPED` only for reproducible trace-level observation of health loss during coast-only model waits, with source hashes and complete per-decision reconciliation. No causal or counterfactual policy claim.
- **C:** Typed samples are intermittent; health may change between them. Temporal association cannot attribute damage to the coast choice or show a different policy would improve survival.
- **U:** Two stochastic runs in one fixture are not independent trials; typed-health observability and clock bounds remain as reported by the original runs. This does not qualify general real-time control or human tempo.

## Execution

Run `audit.py` against the adjacent `research/doom/results` inputs using Python 3.12. The formal run used pinned linux/arm64 `python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`, network disabled, 1 CPU, 512 MiB, 64 PIDs, read-only root, and 16 MiB `/tmp` tmpfs. Candidate and audit each ran once; retries 0.

The first candidate correctly stopped on `cover-1`: it contains motor holds and cannot be classified as coast. That assertion failure is retained in `candidate-initial-failure.txt`; the frozen correction classifies each overlapping program from its submitted steps and counts only waits completely covered by coast-only programs. The corrected candidate was then run once and the independent raw-source auditor once.

## Result

See `result.json` for retained per-decision trajectories, source file hashes, and the bounded decision. The raw event inputs are not copied or modified. The original posthoc result and its `7b7541…78bf71` audit remain unchanged.

`candidate.stdout.json` and `auditor.stdout.json` preserve the two successful command summaries. The scope is four coast-only waits across the two retained traces; two waits (v39 decisions 2 and 3) contain sampled health declines. This identifies observed deterioration under coast, not causal damage from the policy or a benefit of any alternative policy.
