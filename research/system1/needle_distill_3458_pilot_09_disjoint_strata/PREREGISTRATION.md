# Issue #4469 — pilot-09 contract-bound disjoint strata

## H / T / D / C / U

**H — hypothesis.** The stratified near-boundary CORRECT augmentation improves shifted CORRECT recall reliably when band B begins at the public contract lower bound |dx|=.111 while preserving IID, boundary, invalid, false-CORRECT and latency gates. Pilot-08's runner-bound PASS is retained as descriptive only because its band B began at .110.

**T — treatment.** Fresh paired seeds 3490, 3491, 3492. Control uses 2,048 balanced examples per class. Treatment keeps 1,024 balanced CORRECT rows and adds 512 band-A examples with signed |dx| in [.071,.110] and 512 band-B examples in [.111,.149]. Each retains |dy|≤.10, |vx|/|vy|≤.05, confidence [.80,1], visible=1. CONTINUE/WATCH data remain unchanged. Same 6→16→16→3 tanh MLP, AdamW lr .008, batch size 64, 700 fixed steps, paired initialization and minibatch stream. Evaluation/control suites remain exactly #3918. Independent audit checks every assigned row against its band, the excluded gap and crossover, rather than only checking the pooled envelope. The exact public Issue contract excerpt is retained in `ISSUE_CONTRACT.md` and hash-bound in `FREEZE.json`.

**D — decision.** PASS only if every treatment seed meets shifted accepted accuracy≥.95, each class coverage≥.75 and accepted recall≥.95, false-CORRECT fraction≤.005, boundary and invalid controls YIELD, CPU p95<60ms and IID accuracy≥.95; mean paired CORRECT recall lift≥.10; IID drop≤.02; shifted CORRECT-recall SD≤.05; exact assigned-band membership; and zero crossover/gap rows. A model gate miss is FAIL. Any mismatch between source, public contract or independent reconstruction is HOLD. Environment/formal failure is STOP. Exactly one formal allocation, no retries, tuning, replacement or post-result exclusions.

**C — constraints.** Cached local `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, CPU-only, network none, read-only source/root, dedicated writable output, ≤2 CPUs/4GiB/64pids/64MiB tmpfs. No external labels/provider, GUI or execution authority.

**U — limits.** Synthetic hand-authored teacher, one covariate shift, three seeds, one small model. No real-task utility, broad generalization, product safety or execution-authority claim. Any PASS is scoped evidence only, not automatic model promotion.
