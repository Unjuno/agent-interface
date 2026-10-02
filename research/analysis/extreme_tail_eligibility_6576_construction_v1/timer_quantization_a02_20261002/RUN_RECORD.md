# A02 run record — fresh-seed support-rule evaluation

**Disposition: `PASS_SUPPORT_RULE_SCOPED`.** Candidate 1/1 exit 0; independent raw-only auditor 1/1 exit 0 (`AUDIT_VALID`); retries 0.

## Executed allocation

- Allocation `6576-TIMER-QUANTIZATION-A02-20261002`; frozen main `049cc5edb9e020ed31ce2bdc8f8dac45a93f53d8`.
- Dedicated OrbStack VM `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04 arm64; outer cgroup CPU `200000 100000`, memory `4294967296`, swap `0`.
- Private Docker Engine had no running containers at freeze. The shared `unjuno-native-ci-6092` was not used/touched.
- Image `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (linux/arm64), cached; no image pull.
- Candidate container ID `4271cdf09d36d987ba520d6e38bddea9d198e9121fb3b403eab7b41e537b0d51`; auditor ID `4054aaf4398d3b5915cf620bc427a9ba9201e4997c29b64fa73431e089520f52`.
- Both inspected before start: network none, read-only root, 1 CPU, 2 GiB memory, 2 GiB memory+swap (zero swap), `/tmp` tmpfs 64 MiB noexec/nosuid. Source/input and candidate output read-only to the auditor; each process had a distinct writable output mount.
- Frozen input SHA-256 `ce0b0ee997407293e1639ef7acfe419a855dc2bb3206e5a08d5c924ad1d04aef`; 90 fixtures and 360,000 observed training rows.

## Results

The independent auditor recomputed all per-fixture thresholds, block medians, lag-1 correlations, tail counts, distinct support counts, baseline decisions, support-rule decisions, and aggregate rates from the frozen input and candidate output.

| Arm | Fixtures | Current-gate eligible | Added support-rule holds | Conditional hold rate |
|---|---:|---:|---:|---:|
| Continuous q=0 | 30 | 21 | 0 | 0% |
| Rounded q=0.25 | 30 | 24 | 7 | 29.17% |
| Rounded q=1.0 | 30 | 30 | 30 | 100% |

The frozen primary criteria passed: q=1.0 conditional holds >=90%, continuous additional holds <=5%, and both denominators nonzero. Thus the proposed `distinct_tail_values >= 20` rule separated the q=1.0 rounded arm from continuous controls in these fixtures without additional continuous false holds. The intermediate q=0.25 arm shows a nontrivial tradeoff (7/24 held) and must not be hidden.

## Interpretation and scope

This is a method-scoped synthetic follow-up to A01, not validation of 20 as a general sample-size/support threshold. Quantization levels and exponential generator are artificial; current-gate eligibility is a frozen code diagnostic, not proof of stationarity or independence. No EVT/GPD/TailID fit, p99 calibration, tail coverage, timer-device resolution, real release delay, physical key-up, operational deadline, safety or worst-case guarantee was tested. The result cannot justify adopting this cutoff in production without separate preregistered coverage/false-hold work on representative endpoint traces.

Formal six-case #6576 T0 remains separate and uninvoked. No consumed allocation was retried. Full input, source, candidate summary, auditor output, exits and hashes are retained under this directory.
