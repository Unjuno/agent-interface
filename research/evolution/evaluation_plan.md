# Shared evaluation preparation — not a completed qualification study

## Question and decision

Can one pinned candidate preserve the declared input/observation semantics
across the supported environments? This reduces core architecture uncertainty
and tests cross-domain coverage, meeting the experiment selection rule.

Reference candidate: `interactive_v10.py`, full presentation, and its complete
source manifest as published at `7427bdd`. Do not silently switch individual
domains to older runtimes and call that shared coverage. Compact mode is excluded
from the reference because critical visual-event preservation is not established.
No new feature is promoted by selecting this reference for evaluation.

Before execution, record a machine-readable evaluation manifest containing the
exact commit/source hashes, environment versions, scenario IDs/seeds, expected
outcomes, action vocabulary, input limits, clocks and adapter versions. Historical
results do not count as this new suite. No candidate modification mid-suite;
if needed, preserve the failed cohort and start a separately identified revision.

## Capability inventory

Update: the [first readiness cohort](READINESS.md) executed ordinary plus
already-expired-request cases in XTerm, Chromium, Calc and Inkscape (keyboard
nudge). All eight task artifacts and 78 frames audited. This confirms runnable
adapters for those cases; it does not qualify the common semantics under broader
stress or cover the continuous/DOOM adapters listed below.

| Domain | Current reference coverage | Preparation needed |
|---|---|---|
| Terminal/text | Entry point and independent saved-text oracle exist | Fresh task + stale request + cancellation scenarios |
| Browser | Chromium fixture is selectable through inherited suite | Verify task navigation and fresh oracle with this candidate |
| Spreadsheet | Actual Calc self-use exists | Fresh cells, save dialog and focus-recovery cases |
| Graphics/editor | Inkscape fixture selectable; keyboard vocabulary available | Explicit task adapter and correctness check; no new pointer ISA assumed |
| Multi-window/modal | Controlled focus probe and Calc modal evidence | Shared scenario harness, including wrong target, cleanup and recovery |
| Continuous motor | Historical separate tracking runtime | Adapter to this input owner/focus/lease semantics; not currently qualified |
| DOOM real time | Historical separate DOOM runtime | Adapter and normal-speed clock verification under the same semantics |

This is an inventory, not a pass matrix. Inspect the transitive implementation
and pin the adapter before each domain becomes runnable. Shared critical-event
and disconnect handling remain incomplete even when ordinary tasks succeed.

## Two stages

1. **Readiness smoke cohort:** two distinct fresh episodes per runnable domain,
   one ordinary task and one relevant stress scenario. Record unsupported cases
   as not runnable, not passed or a behavioral failure. Fourteen cases would
   cover seven domains when all adapters exist. This stage checks harnesses and
   invariants only; it cannot qualify the three-revision freeze window.
2. **Qualification study:** after readiness, predeclare episode allocation and
   statistical acceptance rules based on exposure and observed variability.
   Cover hidden/fresh/stress cases and the same previously passing invariants.
   Sample-size rationale and acceptable residual rates are still pending; do
   not compute tail-latency or freeze claims from the readiness cohort.

For a performance candidate, use a counterbalanced same-model paired design,
same tasks/seeds/environment, identical tool output limits and reasoning settings.
Keep full presentation in both arms unless presentation is the nominated change.
Separate retries and report unsuccessful attempts and recovery cost. A comparison
that cannot record actual model identity or usage marks these unavailable and
cannot claim same-model token savings.

## Recorded outcomes and gates

- Independent task success and its saved artifact/oracle; program completion
  alone is insufficient.
- Expected destination versus actual delivered input, stale admission, cleanup
  verification, cancellation/expiry and critical-event retention. Deterministic
  invariant violations stop promotion even if aggregate speed improves.
- Capture/context timestamps, input admission/acknowledgement, first image ready,
  selected-output attempt, client receipt, planner response intervals and known
  semantic completion. Missing endpoints stay missing. Quietness is not completion.
- Actual planner boundaries, observations including failed attempts, bytes in
  named representations, actual billed/model tokens if exposed, and task recovery
  cost. Accepted programs are a separate count.
- New taxonomy class versus recurrence; newly introduced regression versus a
  known baseline failure; changed semantic primitives and reviewer churn rating.

Next action: extend the pinned reference to the remaining domains using the
[adapter inventory](ADAPTER_DIFF.md); DOOM is the first transfer candidate.
Continue historical occurrence ordering and declare qualification allocation.
Readiness and active interruption stress already cover four applications, but
neither cohort qualifies a freeze revision.

Before any performance promotion, use the [bundle contract](BUNDLE_EVALUATION.md)
to declare baseline, individual arms, reasonable bundles, interactions and
complexity/portability review. Keep the 10% individual promotion signal separate
from freeze: measured remaining frontier movement is required for saturation.
The collection/qualification design must precede performance claims or Research
Freeze nomination. The ultimate human-tempo goal remains.
