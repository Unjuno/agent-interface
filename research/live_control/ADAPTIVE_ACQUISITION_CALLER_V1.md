# Adaptive acquisition caller v1

Issue #53 identifies two coupled problems: adaptive acquisition branches are
duplicated across runners, and their usage summaries cannot safely represent
optional, failed or omitted calls. `adaptive_acquisition_caller_v1.py` is an
offline-first shared boundary with injected observation, model, evidence,
input and effect-verification adapters.

## Contract

One function handles cold acquisition and warm reuse. Cold acquisition records
source observation, coarse selection, anchor acquisition/review, optional
expansion and expanded selection. Reuse begins from a declared cached target,
runs local revalidation, and either executes, safely stops or enters the same
expansion/selection repair path. Every target reaches a final local
revalidation before the execute adapter. A stale, association, unavailable,
ambiguous, no-match or exhausted outcome exposes no input authority.

The caller writes a `model_attempt_started` journal event before invoking each
model adapter. Attempt and completed-call ledgers are separate. Usage coverage
is counted per field across every attempt, including failed calls with
available usage. A missing field makes that aggregate unavailable rather than
zero. Cached input remains a reported subset and is never added to total input.
Call IDs are checked for duplicates across completed and failed attempts.

Every possible stage is `completed`, `failed` or `skipped` with a reason.
Coarse origin is one of model-produced, caller-provided or injected archive.
Full cold, injected subpath and warm reuse have different comparison classes;
the latter two cannot be accidentally presented as full-cold measurements.
Model identity/settings belong to each recorded model call.

## Offline retained-record block

The probe uses exact usage from three retained OpenTTD reports and typed test
double decisions. The full three-call expansion is a synthetic accounting
composition across retained records, not a new matched efficacy episode.

| Branch | Outcome | Attempts | Input-token aggregate | Comparison class |
|---|---|---:|---:|---|
| cold anchor accepted | verified effect | 2 | 17,386 | full cold |
| cold expanded recovery | verified effect | 3 | 25,675 | full cold |
| injected expanded subpath | verified effect | 2 | 16,387 | injected subpath; coarse omitted |
| cold no-match | safe stop | 3 | 25,791 | full cold |
| cold exhausted | safe stop | 3 | 25,675 | full cold |
| cold stale / association | safe stop | 2 each | 17,386 each | full cold |
| warm reuse | verified effect | 0 | 0 | warm reuse |
| warm invalidate then repair | verified effect | 1 | 8,280 | warm reuse |
| warm association refusal | safe stop | 0 | 0 | warm reuse |

Additional controls preserve delivery uncertainty after authority consumption,
a failed call with missing usage, a failed call with 9,288 input tokens
available, a completed call missing cached-input metadata, and duplicated call
IDs. Fifteen scenarios pass on Windows and WSL.
The independent audit reconstructs source hashes, attempt/completion joins,
usage totals/coverage, duplicate IDs, phase clocks, stage reachability, safe
stops and journal pairing.

The zero-call and one-call reuse branches are test-double mechanics. They do
not demonstrate a token, cost or latency improvement. Monetary costs remain
unavailable. The next required evidence is a frozen live block through this
same caller for accepted anchor, natural full expansion, no-match/exhaustion
and stale/association refusal, followed by a different GUI layout before any
portability claim.

## Evidence

- Implementation: `adaptive_acquisition_caller_v1.py`
- Offline probe: `probe_adaptive_acquisition_caller_v1.py`
- Independent audit: `audit_adaptive_acquisition_caller_v1.py`
- Results: `results/adaptive-acquisition-caller-01/`
