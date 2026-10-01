# Cross-domain typed rule VM v2 — retained result

Decision: **PASS_CROSS_DOMAIN_RULE_VM_SCOPED**.

## Chronology / integrity

- #934 is retained separately as `STOPPED_FORMAL_HARNESS_ADAPTER_HASH`: its single formal invocation crashed before `RESULT.json`; it is not pooled or reinterpreted.
- #935 changed only post-timing output canonicalization for diagnostic `Request` values. `decision_900.py`, `fixture.json`, and `rule_vm.py` are byte-identical to the #934 freeze where declared.
- Fresh #935 formal invocation count 1; reruns/replacements/tuning 0.
- Independent audit: PASS, errors `[]`.
- Postformal source Git-object rehash: exact 6/6.
- RESULT SHA-256: `9fe267edead4d988448ed0d8907600bbb3836b3bc512af724f7c2374efa679ae`.
- AUDIT SHA-256: `2ca186a945e51684a8ae2e97a546964877a200cb961227bd3d3f19d478b371bd`.

## Correctness / transfer

Chromium: common VM matched the exact #900 native decision on **8,192 / 8,192 unique payloads**, errors 0.

OpenTTD retained-state transfer: **5 / 5 exact** using only caller/runtime-visible typed fields frozen from retained evidence:

- 1280 repeat -> `YIELD(TARGET_NOT_REACHED)`;
- 1280 target -> `EXECUTE(CONTINUE_PROGRAM)`;
- 1152 target -> `EXECUTE(CONTINUE_PROGRAM)`;
- 1152 repeat -> `YIELD(TARGET_NOT_REACHED)`;
- post-resolution binding change -> `YIELD(BINDING_CHANGED)` before pointer input.

Four structural controls (unknown/missing guard reason; stale binding even with `met` or `target_not_reached`) all failed closed and never emitted EXECUTE.

`EXECUTE(CONTINUE_PROGRAM)` remains only a proposal for already-authorized later steps. The VM granted no authority, performed no task input, network call, or gradient update.

## Warm batch-1 timing

Environment retained by runner: Linux 6.18.44 x86_64, CPython 3.13.5, reported logical CPU count 5. CPU model/clock were not captured; therefore these values are host-scoped and must not be generalized across hardware.

Each timing arm: 1,024 warmups + 65,536 measured calls.

| domain / path | p50 us | p95 us | p99 us | mean us |
|---|---:|---:|---:|---:|
| Chromium native e2e | 7.040 | 8.421 | 27.127 | 7.733 |
| Chromium VM e2e | 9.786 | **11.763** | 32.351 | 10.537 |
| Chromium VM only | 1.057 | **1.471** | 2.615 | 1.239 |
| Chromium adapter only | 8.708 | 12.271 | 33.726 | 9.933 |
| OpenTTD native e2e | 0.387 | 0.454 | 0.531 | 0.441 |
| OpenTTD VM e2e | 1.640 | **1.880** | 2.203 | 1.768 |
| OpenTTD VM only | 0.809 | **0.988** | 1.067 | 0.857 |
| OpenTTD adapter only | 0.971 | 1.485 | 2.540 | 1.131 |

Do not add adapter and VM percentile values: component percentiles are not the percentile of the composed path. End-to-end timing is measured directly.

The common CPython VM therefore clears the frozen `<10 us VM-only` and `<25 us end-to-end` p95 gates in both domains. Relative native slowdown is not the promotion target: Chromium VM e2e p95 is ~1.40x native and OpenTTD ~4.14x native, but absolute p95 remains 11.763 us and 1.880 us respectively.

## H / T / D / C / U

**H:** one immutable typed rule VM can preserve two retained domains' exact local decisions and fail-closed escalation at microsecond cadence.

**T:** exact #900 source semantics on 8,192 fresh deterministic Chromium payloads plus five pinned retained OpenTTD states and four structural controls; one frozen formal; 65,536 timing calls/path.

**D:** PASS. All semantic, fail-closed, latency, zero-authority/task-input/network/gradient, source integrity and audit gates passed.

**C:** this may standardize execution representation without reducing semantic authoring complexity; domain rules are still domain-specific data. Five retained OpenTTD states are narrow transfer evidence. If the next real residual is exactly expressible in this VM, a learned backend remains unjustified.

**U:** no new live OpenTTD task was run; no second-domain frontier-boundary economics are inferred. CPU model/clock, calibrated timing uncertainty, energy and cost were not recorded. CPython tail outliers exist. This is an execution-ABI result, not a population reliability or intelligence claim.

## Consequence / next discriminator

Retain the common typed decision envelope as the leading **rule-tier** System-1 substrate. Do not promote LINEAR/TREE/NN merely because they are available. The next useful experiment must identify a real Astra-authored repeated decision whose required semantics cannot be represented by this finite rule VM without weakening the task contract. Only then compare LINEAR, TREE, and TTC tiny-policy under the same typed inputs, output vocabulary, UNKNOWN/YIELD, deterministic authority, state-extraction accounting, and frontier-boundary accounting.
