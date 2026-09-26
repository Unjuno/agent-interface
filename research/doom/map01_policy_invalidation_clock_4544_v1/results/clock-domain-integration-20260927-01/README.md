# Host-monitor to Docker-runtime boundary experiment

**Result: `PASS_SCOPED`** — one actual host-side policy monitor receipt was
translated into a pinned Docker runtime clock domain and rejected by the real
final-admission gate without input authority.

## Observations

- Actual `ObservableSignalPolicyMonitor` returned `HARD_INVALIDATED` for the
  controlled health transition 91→68. The timestamp fields came from the
  monitor process's `time.perf_counter_ns()`; the monitor receipt did not
  include a timestamp-domain field.
- Three ordered probes against one persistent pinned `linux/arm64` Docker
  runtime measured conservative lower offset `-739137004730 ns` and upper
  offset `-738791688688 ns` (uncertainty width `345316042 ns`). Receipt age at
  calibration was `353939041 ns`.
- Sending the untranslated host receipt to the runtime-domain gate reproduced
  `ValueError: controller decision precedes observed boundary`.
- The #4544 translator preserved the source receipt, translated its timestamp,
  and the actual `final_action_admission_v1.decide_final_admission` returned
  `REJECTED_POLICY_INVALIDATED`, `input_authority_admitted=false`, and no
  Executor admission. A controller decision before the translated invalidation
  was refused.

## Audit and reproduction

Raw JSON: [`result.json`](result.json), SHA-256
`2e9536f35f52697cda58b43896b95c1c1720792550292821966aee0baecfa60`.

The stdlib-only `audit_clock_domain_result.py` independently recomputes clock
offsets, uncertainty, age, translated timestamps and admission invariants. It
passed and rejected 10/10 semantic corruption controls. Reproduce the boundary
experiment from repository root with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_policy_invalidation_clock_4544_v1/clock_domain_integration_experiment.py
PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_policy_invalidation_clock_4544_v1/audit_clock_domain_result.py
```

The experiment launches only a clock-query process in the locally cached pinned
Docker image, with network disabled and read-only root. It uses the real
current-main monitor, translator and final-admission function. No model call,
game process, GUI interaction, motor input, or formal MAP01 allocation was run.

The complete 20-test pinned Docker regression suite and generated-candidate
controller AST check also passed on this checkout; these are construction gates,
not gameplay/formal evidence.

## Limits

This is a single local host/runtime clock boundary, not a timing distribution.
It supports the #4536/#4544 clock-domain translation mechanism for this
measured instance, but does not explain the separate seed-990641
`running_action_guard` freshness exception: its compared operands were not
logged, and the formal run stopped before policy translation. It establishes
no MAP01 completion, gameplay effect, reliability, or product claim.
