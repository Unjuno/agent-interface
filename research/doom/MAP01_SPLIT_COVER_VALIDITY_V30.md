# V30 split critical-health and bounded-loss validity

V30 is the smallest construction repair for the representation mismatch exposed
by the only v29 live allocation. It leaves v29 and its retained result unchanged.
At construction freeze, no live model or game allocation had run on v30. The
subsequent one-allocation result is linked below without changing this contract.

## Schema and effective predicate

Schema v5 replaces one overloaded absolute floor with three explicit fields:

- `critical_health_minimum`: absolute health below which the cover is no longer
  appropriate;
- `maximum_health_loss`: short-horizon loss the cover may absorb, statically
  bounded from 0 through 20;
- `max_source_age_ms`: lease from 100 through 30,000 ms.

At admission, the local runtime derives:

```text
effective_hard_minimum = max(
    critical_health_minimum,
    fresh_source_health - maximum_health_loss
)
```

This preserves Luna's v29 judgment that health 30 is an absolute critical floor
while preventing that value from silently authorizing 54 points of loss at
source health 84. The short-horizon loss remains explicit, schema-bounded and
reviewable. A critical floor already above fresh health still rejects all prior
cover commands and substitutes input-free coast.

## Model-free retained-trace checks

The v30 test reuses the v29 exact source at health 84. With critical floor 30 and
maximum loss 20, the effective floor is 64; the observed change to 78 is soft and
keeps the already admitted cover. The value 20 in this replay is construction
input, not an output authored by the v29 model.

A second retained replay uses v28 source health 93, critical floor 30 and maximum
loss 13. It derives effective floor 80, coalesces 87 and 81 as soft, then
hard-invalidates at 79. The value 13 deliberately reconstructs the earlier
posthoc floor-80 development case and is not a calibrated optimum.

Schema tests reject a loss greater than 20. Controller tests also keep the
source-below-critical rejection, prior-cover command refusal, matching planner
interrupt, exact cancel and verified empty release checks.

## Monitor clocks

`ObservableSignalPolicyMonitor` v2 retains monotonic timestamps for monitor
receipt, signal extraction completion and outcome evaluation, plus extraction
and evaluation durations. A later live audit can therefore separate observation
delivery, deterministic HUD work and interrupt dispatch. The original v1 stays
frozen so its hash-bound retained replay remains reproducible.

The relevant Windows set passes 43 tests. The v30/v2/HUD subset passes 15 tests
under WSL/Linux, and the v30 CLI reaches argument parsing without model work.

## Remaining gate

This resolved the discovered representation conflict in construction. It did
not yet show what `maximum_health_loss` Luna would author, whether a soft event
would occur during its following live interval, or whether preserving a cover
would improve decision completion, survival, progress, latency or token use.
The subsequent frozen allocation ran once: one admitted nonempty cover absorbed
exact health84→78 as soft, continued seven later input-hold steps, and the same
planner turn completed while the hard cancel/release path remained intact. See
[the retained v30 live result](MAP01_SPLIT_COVER_VALIDITY_V30_LIVE_V1.md). This
single pass does not establish a causal speed, token, survival, or gameplay gain.
