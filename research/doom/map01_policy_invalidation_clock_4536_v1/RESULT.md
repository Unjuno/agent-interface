# Offline regression result — #4536 policy-invalidation clock boundary

**Disposition: `PASS_POLICY_INVALIDATION_CLOCK_TRANSLATION_REGRESSION_SCOPED`.**

This is only the deterministic prerequisite described by #4536. No MAP01
episode, model call, GUI/game input, task action, formal allocation, or GPU work
was performed. Formal allocation count remains **0**.

## H / T / D / C / U

- **H:** Translating the host-stamped policy invalidation into the same runtime
  clock domain should allow the final-action gate to return an explicit policy
  rejection rather than comparing unlike monotonic timestamps.
- **T:** Regression source and constructed receipt are under this additive
  directory. Inputs use the retained v10 iteration-8 clock interval, but the
  hard-invalidation timestamp is an explicit synthetic control, not recovered
  historical raw evidence. The offline tests invoke the existing
  `final_action_admission_v1` helper; no runtime source is changed.
- **D:** All seven tests pass. The unconverted host timestamp reproduces
  `controller decision precedes observed boundary`. Using the interval's upper
  offset maps host `8577269500000` to latest-possible runtime
  `7838100318940`; this is 1,467,019 ns before controller decision
  `7838101785959` and after planner terminal `7838099328334`. Final admission
  returns `REJECTED_POLICY_INVALIDATED`, preserves the host timestamp and
  conversion metadata, leaves `input_authority_admitted=false`,
  `grants_input_authority=false`, and `executor_admission=null`. A boundary one
  nanosecond after the decision, wrong session, malformed/over-wide
  calibration, and malformed host timestamps all fail closed.
- **C:** This establishes the helper contract for a constructed timestamp and
  the retained offset interval only. It does not establish that the historical
  v10 stop was caused by this field.
- **U:** The actual decision-8 invalidation receipt remains unavailable in the
  retained text evidence, so the historical causal attribution remains
  unverified. A fresh one-time formal MAP01 allocation is still required to
  qualify the successor hypothesis.

## Verification

Host:

```text
python -B -m unittest discover -s research/doom/map01_policy_invalidation_clock_4536_v1 -v
Ran 7 tests — OK
```

Local Docker Desktop, cached image
`python:3.13.5-slim-bookworm@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`
(`linux/amd64`), `--pull=never --network none --read-only`, read-only source
mount and 16 MiB `/tmp`:

```text
Ran 7 tests — OK
```

No image pull, dependency installation, network, model, GPU, or source/runtime
mutation occurred. No historical output was edited.
