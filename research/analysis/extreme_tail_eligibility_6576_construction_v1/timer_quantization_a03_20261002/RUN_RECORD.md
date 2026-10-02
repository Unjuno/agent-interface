# A03 run record — cutoff sensitivity across fresh synthetic resolutions

**Disposition: `PASS_CUTOFF_SWEEP_SCOPED`; selected smallest tested cutoff = 8.** Candidate 1/1 exit 0; independent raw-only auditor 1/1 exit 0 (`AUDIT_VALID`); retries 0.

## Execution

- Allocation `6576-TIMER-QUANTIZATION-A03-20261002`; base main `aa0311f4501be749c117cbc3c73e5bd3f13bf744`.
- Dedicated OrbStack VM `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04 arm64; outer cgroup CPU `200000 100000`, memory `4294967296`, swap `0`.
- Private Docker Engine; no shared native-CI daemon/container. Candidate container `d4f73e2440f0bfbd85315e8b70b5f0aade94c82bcb18d9fa36186e51e3ce219e`; auditor `55c5a382428b6647b3bf99b770c596a1f028371ca5b181d20e5e1dfad6005dc5`.
- Pinned image `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, linux/arm64; network none, read-only root/source/input, separated outputs, 1 CPU/2 GiB/zero swap, `/tmp` tmpfs 64 MiB noexec/nosuid. Config inspected while both containers were created and not yet started.
- Frozen input SHA-256 `2802756348963c0c5d71edab270c7d09c781e298ad371ffdfbe3f40e36be4685`; 200 fixtures, 50 per resolution arm, 800,000 observed training values.

## Conditional hold rates

Denominators include only fixtures that passed the existing frozen eligibility diagnostics.

| Arm | Baseline eligible | cutoff 8 | cutoff 12 | cutoff 16 | cutoff 20 | cutoff 24 |
|---|---:|---:|---:|---:|---:|---:|
| Continuous q=0 | 31/50 | 0/31 (0%) | 0/31 (0%) | 0/31 (0%) | 0/31 (0%) | 0/31 (0%) |
| Rounded q=0.25 | 36/50 | 0/36 (0%) | 0/36 (0%) | 0/36 (0%) | 14/36 (38.89%) | 35/36 (97.22%) |
| Rounded q=0.5 | 2/50 | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| Rounded q=1.0 | 50/50 | 48/50 (96%) | 50/50 (100%) | 50/50 (100%) | 50/50 (100%) | 50/50 (100%) |

Cutoffs 8, 12, and 16 meet the frozen primary criteria; 8 is the smallest. Cutoff 20 fails the q=0.25 <=10% condition (38.89%), while 24 holds 97.22% of q=0.25 baseline-eligible fixtures. q=0.5 is weakly identified for this comparison because only 2/50 pass the pre-existing gate; its conditional rates are descriptive, not a robust validation stratum.

## Interpretation and limits

The fresh-seed finite sweep supports cutoff 8 over 20 for this exact synthetic generator, sample size, and resolution grid. It does not establish cutoff 8 as a universal or production rule. The 20-distinct criterion's generality, actual measurement quantization, real release endpoints, stationarity, dependence, EVT/TailID fits, p99 calibration/coverage, safety deadlines, physical key-up, and worst-case claims remain untested. Formal six-case #6576 T0 remains a separate uninvoked allocation. All source, input, candidate summary, independent audit, exits, and hashes are retained here.
