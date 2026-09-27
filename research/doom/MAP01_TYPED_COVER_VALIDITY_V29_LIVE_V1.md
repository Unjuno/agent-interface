# Frozen v29 planner-authored cover-validity result

`map01-typed-cover-validity-v29-live-01` is the first and only run of the
preregistered v29 allocation. It uses the same hash-bound real Freedoom MAP01
tic-1263 threat fixture as v28, six Luna-low decisions and one continuously
advancing X11 game. The exact reviewed initial frame and every decision frame
show an enemy.

## Result

The run is retained as
`RETAINED_TYPED_ENVELOPE_SOFT_UNEXPOSED_WITH_AUTHORED_FLOOR_REJECTION`.

- All 109 exact observations produce a health signal; unknown reads are zero.
- Reviewed decision health is `100, 97, 90, 84, 84, 78`; ammunition is
  `50, 50, 50, 50, 48, 48`.
- Four decisions hard-invalidate and finish interrupted/ineligible. Their
  dependent actions admit no plan input.
- Decisions 3 and 5 complete with eligible schema-v4 actions. Both author the
  absolute health floor 30 with a 30-second lease.
- At decision 4, current health is 84. Floor 30 would allow 54 points of loss,
  beyond the frozen 20-point construction safety bound. The runtime rejects all
  three proposed prior-cover commands and runs input-free coast.
- No authored envelope is admitted during a later changing-health interval.
  Consequently soft transitions are zero and the central liveness mechanism is
  unexposed.
- Six covers and two primary programs all reach terminal with verified empty
  key/button release. The two primary programs complete; all covers are
  cancelled. There are no cover renewals.
- The final state is alive and unfinished after 30.018512445 seconds with zero
  kills, deaths or exit. Model intervals total 25.447387863 seconds.

V28 completed one of six decisions and interrupted five; v29 completes two and
interrupts four. V29 also takes longer than v28. Since no v29 soft transition
occurs, neither difference can be attributed to the typed envelope.

## Latency and usage

For the four hard events, capture-to-interrupt-send is 91.568–94.063 ms,
interrupt-send-to-completion is 2.084–3.816 ms, and capture-to-verified cover
release is 99.514–105.595 ms. V29 failed to retain a separate monitor-detection
timestamp, so capture-to-send includes observation delivery, health extraction
and controller dispatch. It cannot be compared directly with v28's
detection-to-send metric.

Three usage notifications appear. The first completed turn reports 10,640
input / 7,936 cached / 176 output / 40 reasoning tokens. The interrupted fourth
turn repeats that cumulative receipt and is not added. The final completed turn
brings known cumulative completed-turn usage to 22,484 input / 18,176 cached /
366 output / 84 reasoning tokens. Other interrupted-turn use is unknown rather
than zero.

## Finding

The safety rejection is correct, but the output contract combines two meanings
in `hard_minimum`:

1. the absolute health below which the policy is no longer appropriate;
2. the amount of near-term health change that the current cover may absorb.

Luna's repeated value 30 is coherent as a critical survival floor and too broad
as permission to absorb 54 points from health 84. A local 20-point cap prevents
unsafe authority, but turns that semantic mismatch into rejection and leaves
the liveness path unused.

The next contract should keep an absolute `critical_health_minimum` and add a
schema-bounded `maximum_health_loss`. At admission, the effective hard floor is
the greater of the critical floor and `source_health - maximum_health_loss`.
This preserves the model's absolute judgment while making the short-horizon
tolerance explicit and locally bounded. The monitor must also retain receive,
extraction-complete and invalidation timestamps before another allocation.

## Limits

This is one nondeterministic model sequence from one fixed state. It establishes
safe rejection, exact health monitoring and hard-path release under threat. It
does not establish soft preservation, improved planner completion, survival,
gameplay, latency, tokens, reliability, human tempo or MAP01 completion.

## Reproduce the audit

```powershell
python research/doom/audit_map01_typed_cover_validity_v29_live_v1.py
```

The retained result, hashes, contact sheet and audit are in
`research/doom/results/map01-typed-cover-validity-v29-live-01/`.
