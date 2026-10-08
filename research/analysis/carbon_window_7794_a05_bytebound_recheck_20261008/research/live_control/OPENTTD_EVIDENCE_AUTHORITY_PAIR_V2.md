# OpenTTD evidence target authority pair v2

## Retained v1 failure

The first preregistered pair replaced the forced-selection contract but made the
shared anchor prompt too abstract. It said only to choose from receipts and
omitted the condition's target noun. Luna-low therefore accepted the injected
wrong anchor receipt instead of expanding. The driver stopped before expanded
selection or target input. Eight durable calls, 29 exact frames, 8,112 input
tokens, zero button-downs and clean process/input release are retained. No retry
was made under v1.

## V2 correction

V2 changes only the anchor prompt: `Company Finances` is present at both
decision boundaries in the positive condition, and `Airport construction` is
present at both boundaries in the no-match condition. Both fresh private GUI
sessions otherwise use seed991004, the `[21,28]` observed surface translation,
the same injected wrong anchor, the same five screen-derived toolbar receipts,
Luna-low and the same runtime authority checks. Cached schema compatibility is
verified before the first GUI with zero endpoint calls.

## Result

| Condition | Authority | Diagnostic | Target button | Calls | Exact frames | Input tokens | Decision to evaluation |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Company Finances | `TARGET_REFERENCE_ONLY` | `matched` | 1 | 18 | 52 | 16,489 | 26.774s |
| Airport absent from five receipts | `NO_TARGET_AUTHORITY` | `no_match_in_observed_set` | 0 | 12 | 41 | 16,503 | 18.694s |

Positive selects receipt5 `[506,79]`, exactly rehovers its tooltip, releases the
only button program and passes the translated independent Company Finances title
oracle. No-match cites no receipt or point and never enters rehover, clear or
click. Both first reject the wrong anchor and collect the complete five-receipt
set.

Across the pair, four model calls report 32,992 input tokens, including a 6,912
cached subset, plus 477 output and 237 reasoning-output tokens. The pair uses 30
durable calls and 93 exact frames. Initial anchor hover replies take 1.285s and
1.288s. Semantic selection arrives at 21.968s and 17.985s. These sequential
values are descriptive; they do not prove a speedup.

Windows and WSL audits reconstruct both model outputs, all frames, cache/source
hashes, releases, target inputs and the positive oracle. No subagent or retry
participates. Decision: `RETAIN_EVIDENCE_TARGET_AUTHORITY_PAIR_V2`.

## Scope

This is one fixed-seed pair with a deterministic wrong-anchor injection. It
demonstrates a live executable non-selection path and a preserved positive path.
Together with the Mindustry candidate-stage and unreadable-receipt stops, it
covers Issue #52's bounded branch mechanics. It does not estimate natural model
error, broad reliability, causal speed, token reduction or human tempo.

## Issue #52 acceptance evidence

| Required branch | Authoritative evidence | Result |
| --- | --- | --- |
| Positive receipt selection and task completion | This v2 Company Finances condition | One target button; translated title oracle verified |
| Valid receipts with no matching target | This v2 Airport condition | `NO_TARGET_AUTHORITY`; no point; zero target buttons |
| Candidate-stage bounded stop | Retained Mindustry viewport-excluded condition | No world hover or placement; raw `ambiguous` diagnostic preserved |
| Unreadable receipt | Retained Mindustry unreadable condition | `NO_TARGET_AUTHORITY`; zero placement buttons |
| Ambiguous, unavailable and exhausted evidence | Contract v2 recorded controls | Each maps to `NO_TARGET_AUTHORITY` without a receipt or point |
| Changed or mismatched receipt association | Contract v2 invalid controls | Wrong point and invalid receipt combinations are refused |

The positive and negative task outcomes remain separate from whether the
authority decision was correct. Probe motion is counted as GUI input; “zero
target buttons” does not mean that the no-match condition performed no probes.

Primary artifacts:

- `results/openttd-evidence-authority-pair-01/audit.json`
- `results/openttd-evidence-authority-pair-02/preregistration.json`
- `results/openttd-evidence-authority-pair-02/report.json`
- `results/openttd-evidence-authority-pair-02/audit.json`
