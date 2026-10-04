# Native WSL vs WSLc memory comparison — #7430 A01

Status: preregistered successor; **HOLD before candidate**. This path retains
the first environment-gate outcome and contains no candidate or auditor data.
The hypothesis and acceptance rules follow open Issue #7430. At the time of
the first preflight, its detailed protocol specified 12 sequential paired
blocks while the final cost paragraph said six. A01 interprets the explicit T
and D sections (12 pairs) as authoritative. The issue body was subsequently
corrected to say 12 pairs; the original mismatch and first outcome remain
retained here.

## H / T / D / C / U

- **H:** For this exact low-memory finite CPU workflow, native WSL preserves
  byte-identical candidate/auditor behavior and reduces paired median
  incremental host-visible WSL VM peak working set by at least 15% versus
  WSLc. Linux process-tree peak RSS is reported separately.
- **T:** Fresh A01 successor to A03's belief-replay candidate and independent
  auditor, frozen against main `510c98fe46889461dce2a4c0e14e261eaa47e8ed`.
  Issue #7430 calls for 12 sequential pairs, six in each arm order, with order
  assigned from a frozen random seed; per-run process-tree RSS, cgroup metrics
  only if available, Windows-visible `vmmemWSL` working set relative to
  pre-run baseline, immediate/30-second post-run values, and guest
  `MemAvailable`/swap/PSI context. No pressure induction, Docker, WSL restart,
  `.wslconfig` change, GUI, GPU or concurrent experimental run.
- **D:** `PASS_MEMORY_SCOPED` requires all 12 pairs complete without retries,
  byte-identical candidate outputs and independent audits, at least 15%
  median paired host-VM peak reduction, and two-sided paired sign test p<0.05.
  Correctness without the memory criterion is `PASS_CORRECTNESS_ONLY`;
  output/audit mismatch is `FAIL`; attribution limits, accounting mismatch,
  competing work or uncontrolled background load are `HOLD/STOP`.
- **C:** Python/libc differences, cache state, WSL VM reclaim, Windows process
  accounting, sample interval and unrelated workloads can confound the result.
  Guest RSS is not host VM working set and these counters must not be added.
- **U:** One synthetic workflow on one Windows/WSL host only. No Docker
  comparison, hard-limit/OOM claim, general memory-saving claim or inference
  about GUI/model/GPU/long-lived work.

## First outcome — preflight only

At 2026-10-04 04:12 UTC, before any A01 candidate or auditor:

- Checkout was clean at main merge `510c98fe46889461dce2a4c0e14e261eaa47e8ed`.
- The four A03-qualified source files materialized on that main have these
  hashes: `fixture.json` `374a6136bc5a0b5cfe39cce915625505c6a56cade870b20fb2e749aa4e7fe9d7`,
  `candidate.py` `972b711c3a6c57e09d48652884c96491a70c5ef7ea183e96b052692c6bddee0a`,
  `runner.py` `31a13ac9dee59d4d7d58fa7cb5c94afc9418477ca22d644459d6d01acf76ccdc`,
  and `audit.py` `81fe3dc715afb4f9e2039a513157f608fddfef950643e0bdd6431350f3a4ad4d`.
  A03's shared staging runner was frozen at
  `459034c71a1ece158b532141ebe79e20b88f07f6f02eb576c223a15a62d43dea`.
  These identities do not mean A01 runtime/image gates passed.
- Ubuntu WSL2 had **17** extant `native_mcp_v1.py` processes, all using
  `results-local/native-host-integration-03` (Calc/Inkscape, seed 991315).
  They were read-only observed; no process was stopped or modified.
- A process snapshot showed five WSLc CLI processes; attribution of those
  processes (including whether one was this allocation's diagnostic) is
  unknown. The read-only `wslc.exe container ls --quiet` request produced no
  output after more than 20 seconds and was interrupted locally. Thus an idle
  WSLc gate could not be established. No container was started, stopped,
  inspected, or removed by this allocation.
- `vmmemWSL` was 305,532,928 bytes and `vmmemwslc-cli-junny` was 502,132,736
  bytes in one instantaneous host snapshot. These are context only, not
  baseline/peak measurements and not attributable to A01.
- Guest snapshot: `MemAvailable=4,943,208 kB`, `SwapFree=2,047,636 kB`, memory
  PSI `some/full avg10/60/300=0.00`. These are one-time context readings, not
  clean-host evidence.
- Disposition: **HOLD_ACTIVE_COMPETING_WORK_AND_WSLC_GATE_UNAVAILABLE**.
  Candidate=0, auditor=0, retry=0. No memory statistic is inferred from this
  preflight.

This hold does not supersede A03/A04, consume a candidate, or authorize
terminating concurrent work. A fresh preflight is required before a new A01
attempt, after the observed competing allocation ends and WSLc idle/image
inventory responds. Preserve this first outcome unchanged.
