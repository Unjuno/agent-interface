# WSLc Chromium: persistent-first, new-seed lifecycle block

This preregistered block follows the forward and reverse lifecycle comparisons. It moves persistent to **first** and changes the fixture seed from 991028 to 991029; both changes occurred together. The host/launcher/source snapshot, requested model, image, limits and lifecycle boundaries otherwise match the prior harness, with the seed literal changed in the runner. Each arm has a new process, session and isolated container, and its own schema preflight. Since the seed also changed, this is not an isolated test of order.

| Allocation | Arm | Outcome | Exact submissions | Time to both process returns | Known input tokens, including preflight |
| --- | --- | --- | ---: | ---: | ---: |
| at01 | persistent | completed | 6/6 | 37.537 s | 36,896 |
| at02 | plain | completed | 6/6 | 39.652 s | 104,140 |
| at03 | ephemeral | incomplete | 5/6 | 161.097 s | at least 86,342; final request usage unavailable |

The successful pair gives a 5.33% shorter defined lifecycle for persistent in this block, versus 18.86% and 19.42% in the prior two same-seed blocks. Changing seed and position together, independent model sessions, provider timing and cache make a causal attribution impossible. These observations do not establish general speed, cost, fault parity, reliability, or MAP01 completion. Cached tokens are included in input, not added. Provider cost is unknown. The at03 elapsed time ends after the failed wait and cleanup; it is **not** a successful task-latency observation and must not be averaged as one.

At03's host recorded `PermissionError` after five completed task responses. The sixth request and image were written but no response or model-call result was retained; the caller's sixth attempt timed out with `usage=null` and no call ID. The exact failed file operation is not identified by the retained error. Do not count the missing usage as zero or assert an unobserved provider outcome. Five fixture submissions were exact, task 6 was missing, and all 42 recorded terminal release events were neutral. Both processes returned and post-run WSLc listing found none of the three named containers. No allocation was retried. This failure is a limitation of the experimental shared-volume IPC path, not evidence that the underlying runtime completed or failed its sixth GUI operation.

For completed arms, the timer covers host/preflight startup, schema validation, container/app startup, all tasks, independent fixture scoring, cleanup and orchestration. It excludes launcher bootstrap, source preparation, image build/pull and post-run audit. Source and host-source manifests were checked before and after; excluded source trees and private protocol logs remain local and are hash-indexed. The hosted model service and all host dependencies are not frozen. Raw results, including the failed request and finite timeout, are retained in `public.zip`.

Run `python audit.py` without optimization and with `jsonschema`. It revalidates schema responses, image/response usage for known calls, exact fixture history, recorded terminal releases, timing order and the failed sixth attempt. Source-tree hash verification is a retained local observation, not re-execution of omitted source files. The audit reports at03's known usage as a lower bound and leaves the failed request usage unavailable.
