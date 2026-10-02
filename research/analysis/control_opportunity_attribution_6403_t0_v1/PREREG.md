# Issue #6403 T0 preregistration

## H / T / D / C / U

- **H (hypothesis):** A source-bound control-opportunity timeline can distinguish, on six synthetic traces, no feasible human opportunity, an opportunity, an exercised correction, and an evidence-insufficient case without equating notification sent with notification delivered or agent causation with human exculpation.
- **T (test):** Run one frozen candidate over the six fixture traces, then one separately implemented evidence-only auditor. Require exact agreement with the prewritten oracle, complete trace coverage, independently reconstructed timelines, equal fact access in both summary formats, raw-record references, and rejection of six prespecified corruptions.
- **D (data):** Six fixed synthetic trace records covering (1) effect before notification, (2) sent but undelivered, (3) accepted handoff with sufficient time, (4) ambiguous delivery/attention, (5) stale UI blocking override, and (6) verified correction. Two deliberately misleading responsibility narratives are non-authoritative and must not appear in primary summaries. No people, live user data, model, or GUI are involved.
- **C (controls):** Oracle is mounted only in the audit container and is not readable by the candidate process. Actor/outcome and control-timeline summaries receive identical `presentation_fact_ids`. The auditor is separately implemented and does not import candidate code. Six mutations must fail: sent-as-received, effect moved across the feasible window, hiding a safe override, injecting an oracle label, promoting a negative-control narrative to authoritative, and displaying that narrative in a primary summary. Source correction requires bidirectional negative controls; factual reconstruction is primary and blame is not ground truth.
- **U (uncertainty):** This is a method-only synthetic fixture result, not evidence about human behavior, actual product delivery/attention, causal responsibility, blame, model performance, or operational safety. `UNKNOWN` is not converted into either blame or exculpation. Time values are ordered fixture units, not measured human reaction-time estimates.

## Frozen provenance and execution

- Repository: `Unjuno/agent-interface`; intake base: `121f531be30c3169ebdf49ac06556496896ff28d`.
- Issue body+comments snapshot digest at intake: `4e9c7c75033142da2d7bb5867ee96b659be484889fe3a6122ff8d5ff822dd527` (SHA-256 of `gh issue view --json state,title,body,comments` JSON stream).
- Source correction comment body digest: `fec7d5dfb720a52b97ede56c2068dac1b8e12b4259ea4a7f20896428af321a67`.
- Runtime: local OrbStack Docker, image `python:3.12-slim`, pinned local image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/arm64`). Network disabled; one CPU; 512 MiB memory; 64 PID cap; read-only root and bind mounts; all capabilities dropped; no-new-privileges.
- Construction check passed before freeze. The first attempted container invocation lacked its bind mount and failed before executing package code; it is a setup failure, excluded from the formal run. Corrected isolated construction check passed and rejected all six mutations.
- Formal procedure: candidate exactly once in a container containing only candidate and fixture; if candidate exits successfully, independent auditor exactly once in a separate container with fixture, oracle, auditor, and candidate output. No reruns or retries. Preserve stdout, stderr, exit codes, timestamps, and SHA-256 digests.
- Primary endpoint: evidence-reconstruction gate `PASS_METHOD` / `FAIL_METHOD`; no subjective blame endpoint.

## Decision rule

`PASS_METHOD` requires six of six exact classifications, timeline reconstruction, equal fact access, evidence references, and all six mutation rejections in the pre-run construction check. Any deviation is `FAIL_METHOD`; an infrastructure failure before candidate execution is `STOP_INFRA` and is not retried. Even a pass supports only the narrow method claim above.
