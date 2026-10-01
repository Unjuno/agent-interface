# Safe-probe X11 observation-only R2 — retained result

Issue #1899. Parents #1716/#25/#30. Direct predecessor #1874.

## Disposition

**PASS_SAFE_PROBE_X11_OBSERVATION_ONLY_R2_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## Fixture and safe envelope

One private Xvfb allocation exposes two mapped Tk windows A/B and one fixture-owned X11 property `_AI_CAP_MODE`. Four authored states combine focus={A,B} and capability={0,1}.

Fixture setup sets focus/property before each case. Candidate probing runs through a separate read-only Xlib module.

Safe probes:
- FOCUS_QUERY: XGetInputFocus, declared request/reply cost1, partition [2,2].
- CAP_QUERY: read `_AI_CAP_MODE`, cost1, partition [2,2].
- FULL_QUERY: focus + property + geometry, cost3, partition [1,1,1,1].
- GEOMETRY_QUERY: cost1, partition [4].

`MUTATING_DIRECT_STATE` is an unsafe metadata-only perfect discriminator with no executable implementation.

Declared cost is X11 request/reply count, not latency or utility.

## Formal

256 logical cases,64 per hidden state:

- exact state identification: optimal256/256, greedy256/256;
- optimal #1874 tree: exactly2 safe probes / declared cost2 on256/256;
- #1836-style one-step residual greedy: FULL_QUERY / declared cost3 on256/256;
- unsafe probe executions:0;
- candidate state mutations:0;
- focus/property before==middle==after==final:256/256;
- observed FOCUS/CAP/FULL/GEOMETRY partitions exactly [2,2]/[2,2]/[1,1,1,1]/[4].

Primary audit passes5 corruption controls. Independent audit reconstructs state and declared cost from raw receipts without importing candidate probe implementation; checked_rows256/errors[].

## Construction stop retained

The first construction attempt stopped before scientific row0 because python-xlib attempted a missing `/opt/xvfb/.Xauthority` even though Xvfb used `-ac`. The repair only supplied an explicit empty XAUTHORITY to the private fixture connections. H/T/D/C/U, probe models, costs and corpus were unchanged.

## Interpretation

The analytical safe-probe tree transfers to a real backend read path: a robust runtime can combine two cheap observation-only queries rather than pay for one broader exact query, while keeping a state-changing perfect discriminator outside the eligible set.

This is not evidence that arbitrary GUI probes are safe. The capability bit is synthetic and fixture-authored, and fixture setup itself mutates focus/property only to create independent cases.

## Integrity

- source bundle Git blob: `a6de9827bd90d24eefa17d322218ceb5ef189578`;
- formal raw SHA-256: `b0cff46a11e8ced83ce6bc70192a3142c59f11c4474356588a47b66c52f02fc9`;
- primary audit SHA-256: `e04b0e38e7338b37adc0b65379f2caf43fa33f79251dd119a223e0481da37d29`;
- independent audit SHA-256: `7032e81da9c0563d6ebc315a65cebf64c6ac6c976772737c2c3e570b616b05eb`.

The full729,128-byte row result is cryptographically identified but not embedded; main retains exact source, aggregate result and both audits.

## Scope / next rung

Private same-host X11 only. No XTEST/task input/model/token/latency/human-tempo/general-GUI claim.

A next transfer should replace the synthetic capability property with a real read-only capability or mode source, while preserving the observation-only safe envelope. Do not introduce state-changing discovery probes merely because they are informative.
