# V39 paired-signal boundary construction A01

## Scope correction after review

A01 records reason classification and duplicate-projection behavior only. For mismatch cases, its candidate stores the reason string and discards the returned `outcome`; therefore A01 does **not** audit the fail-closed authority/decision flags. The original one-run candidate, raw output, and source snapshot remain unchanged. Additive A02 preserves full outcomes and independently checks the fail-closed fields and mutation controls: [PR #7966](https://github.com/Unjuno/agent-interface/pull/7966).

## H/T/D/C/U

- **H:** Current-main V39 paired health/ammo monitoring accepts coherent evidence and returns the expected invalidation reasons when sequence/capture/binding diverges, a hard signal floor is crossed, or duplicate projections disagree.
- **T:** Extract and execute the exact current-main helper/class definitions from `map01_overlap_controller_v39.py`; provide stub guard/reader interfaces; evaluate nine cases.
- **D:** PASS only when the candidate's valid/fault case reasons match the frozen expectations. A01 does not establish outcome authority flags.
- **C:** Exact helper/class code is used, but readers and guards are stubbed; this does not exercise source-to-frame integration, live event ordering, or invalidation timing.
- **U:** A passing classification check says nothing about real threat detection, cancellation latency, physical key release, useful feedback, recovery, survival, progress, or MAP01 exit.

## Run

One WSLc candidate run, network disabled, configured 1 CPU and 512 MiB. The host reported unavailable swap-limit/cgroup support; configured memory was limited without swap. The freeze, raw result, source, and hashes remain in this package.
