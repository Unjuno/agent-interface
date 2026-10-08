# Construction-only result — seed 735014

Issue: [#4895](https://github.com/Unjuno/agent-interface/issues/4895)  
Allocation: `needle-online-lora-role-rehearsal-20260927-v1`  
Formal seeds 735211, 735311 and 735411 are untouched.

## H / T / D / C / U

- **H:** A 16-row A rehearsal memory paired into every online B update may preserve A while retaining B acquisition, relative to a shape-matched duplicated-B control.
- **T:** Excluded construction seed 735014; exact cached Linux/amd64 CPU image; Docker network disabled, pull never, source/root read-only, 1 CPU, 2 GiB and 64 PIDs. One full construction trainer invocation (400 base + 3×128 adapter steps) and later separate auditor invocations over the same immutable raw. No formal seed was used.
- **D:** Current construction audit: `PASS_CONSTRUCTION_AUDIT`, 0 errors; base training/snapshot, base immutability, disjoint split/role labels, all 128 optimizer states/predictions per arm independently replayed. Raw 321,131 bytes, SHA-256 `80cfad951bf8739fa130f5213f198282cee4d452b7434879f4396b927a90a1e6`. B_ONLY terminal A/B=0.000/1.000; B_DUPLICATE_CONTROL=0.000/1.000; A_REHEARSAL=0.969/0.281. Construction-only signal: rehearsal preserved A on this seed but substantially reduced terminal B. Curves were non-monotonic. This does not change gates and is not formal evidence.
- **C:** An initial construction wrapper stopped before `runner.run_seed` because it placed its logs inside the runner's required-empty output mount; optimizer updates=0. The corrected wrapper isolated `/raw`, then ran seed 735014 once. The original STOP/logs and later successful raw remain separate. The raw was re-audited with an added explicit post-training base-immutability check; no trainer rerun.
- **U:** One synthetic seed and fixed 16-row memory. It establishes only construction executability and a possible retention/acquisition tradeoff, not a formal effect, role-network skill, live Needle performance, GUI transfer or runtime readiness.

Maximum individual update times were 2.661 ms (B_ONLY), 1.544 ms (B_DUPLICATE_CONTROL), and 0.376 ms (A_REHEARSAL). A separate zero-update Docker construction suite passed 7/7, including arbitrary host output-path mount validation. Docker emitted the image's missing-NumPy initialization warning; the harness uses no NumPy APIs.
