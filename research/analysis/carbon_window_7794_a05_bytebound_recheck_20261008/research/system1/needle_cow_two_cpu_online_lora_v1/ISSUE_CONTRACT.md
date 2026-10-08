# Issue contract — #4769

- Title: Successor #4653: test 2-vCPU COW Needle LoRA during 60-Hz inference
- Allocation: `needle-cow-two-cpu-online-lora-4769-v1`
- Branch: `research/needle-cow-cpu-parallel-4769-v1-20260927`
- Additive evidence path: `research/system1/needle_cow_two_cpu_online_lora_v1/`
- Base: main at freeze; exact SHA in `FREEZE.json`
- Fresh seed block: 9765101, 9765203, 9765307
- Paired CPU quota treatment: 1 vs 2 vCPUs; all other workload factors fixed
- Formal allocation count: one; no retries or seed replacement
- Decision labels and limitations: `PREREGISTRATION.md`

Pre-freeze duplicate checks on 2026-09-27 covered open and closed Issues,
all-state PRs, branch names, main-branch code, commits, and the exact path.
All three seed searches returned zero matches in every category. The current
Issue itself contains the planned seeds; that self-mention is excluded from
the frozen collision list and every other Issue match must remain empty.

The #4653 branch/result is historical reference only. Its frozen seed list and
actual audit rows disagree; this study neither repairs nor reinterprets those
files. The new auditor rejects any such identity mismatch.
