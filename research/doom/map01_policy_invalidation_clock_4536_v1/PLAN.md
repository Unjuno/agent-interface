# #4536 policy-invalidation clock translation — offline regression

## Scope

This is a deterministic, authority-neutral regression for the host/runtime
clock boundary implicated by #4516/#4532. It does not replay a MAP01 episode,
call a model, send input, or revise any predecessor evidence. The historical
policy-invalidation receipt was not retained; this test uses an explicitly
constructed hard-invalidation receipt and the retained iteration-8 clock
interval only to verify the conversion contract.

## H / T / D / C / U

**H** — Translating the host-stamped `outcome_evaluated_ns` to the runtime
clock domain, while retaining the original timestamp and calibration interval,
allows final admission to return `REJECTED_POLICY_INVALIDATED` instead of
comparing unlike monotonic clocks. It must never admit the interrupted answer.

**T** — Use only Python standard library plus the existing pure receipt helper.
Retained iteration-8 decision values: controller host `8577271870833`, runtime
`7838101785959`, offset interval
`[-739170084874, -739169181060]`; planner terminal runtime
`7838099328334`. Construct a host-side hard-invalidation timestamp between
planner completion and controller decision. Convert using the interval's upper
offset (latest possible runtime timestamp), and preserve both domains. No
network, GUI, game, model, GPU, or task input.

**D** — PASS only if (1) the unconverted mixed-domain control raises the
existing boundary-order error, (2) the translated receipt is explicitly
`REJECTED_POLICY_INVALIDATED`, (3) input authority remains false and no
executor admission exists, and (4) malformed receipt, wrong session, stale
calibration, over-wide interval, and a translated boundary later than the
decision all fail closed.

**C** — This proves only deterministic helper behavior for a supplied
same-session offset interval. It does not prove the historical v10 invalidation
occurred at the constructed timestamp or establish the exact cause of its
exception.

**U** — Raw v10 events/protocol are integrity-bound by PR #4532 but are not
available to this offline test as ordinary text through the current connector.
The exact predecessor invalidation timestamp and its provenance remain
unreconstructed. A fresh formal allocation, if this regression passes, must be
separately frozen and executed once under #4536.

## Frozen local discriminator

Use the conservative latest possible runtime mapping
`runtime_ns = host_ns + offset_upper_ns`. Admission is rejected unless this
converted time is no later than `controller_decided_runtime_ns`. Calibration
must be for the same session, have nonnegative integer timestamps, and have
uncertainty width at most 1 second. The conversion adds evidence fields rather
than deleting the original host timestamp.
