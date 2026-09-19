# Existing Calc traces: correction cost accounting

This is analysis of two previously completed primary-assistant WSL runs, not a
new experiment or a container-gate result. The same seed/task and initial request
were used. Zero gap initially displayed 30 instead of 300 and required a repair;
the explicit 2ms successor saved 300/758 without repair. The initial zero-gap
error has screenshot evidence, not an intermediate saved-workbook snapshot.

| Recorded interval | Zero gap, with repair | 2ms, no repair |
| --- | ---: | ---: |
| Explicit submissions, including no-input finish | 4 | 2 |
| Input programs | 3 | 2 |
| First submit entry through final submit return | 55.070 s | 17.164 s |
| Sum of SDK submit spans | 1.943 s | 1.226 s |
| Intervals between those SDK calls | 53.128 s | 15.938 s |

Run `python3 runtime/results/native-calc-recovery-accounting-01/account.py`.
It reads the retained full response lines, checks nonnegative timestamps and
verifies that SDK spans plus inter-call intervals exactly equal the total.
manifest.json hashes the two original response files and the accounting script;
this README was added later. Raw timestamps are WSL monotonic times, with startup
and final owner-status calls excluded from both totals.

The extra correction occurred in the zero-gap run, but the 37.907s difference
must not be attributed solely to pacing. The successor also used finish_after
at confirmation, while the failed run separately inspected, repaired and finished.
Presentation, request assembly, assistant deliberation, commentary and host
scheduling are mixed inside the inter-call intervals. Actual served-model
identity/context equality, host load and ordering were not controlled. This is
descriptive recovery overhead, not an average recovery cost, causal speedup,
human-baseline comparison or model-token/cost result.

The evidence supports retaining explicit pacing as a selectable policy and
measuring correction/extra decision boundaries alongside backend time. It does
not justify reducing observation at an unknown dialog or changing shared delays.
Original zero-gap evidence is on commit 242f6950b under
runtime/results/native-mcp-relay-calc-01; the successful successor is in
runtime/results/native-mcp-managed-paced-01. Their outcome/release audits are
separate from this timestamp accounting.
