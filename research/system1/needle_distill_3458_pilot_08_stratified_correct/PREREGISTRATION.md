# Issue #4462 — pilot-08 stratified near-boundary CORRECT augmentation

Successor experiment for the concrete local Needle research question in #3458. Preserve pilot-05/#3847, pilot-06/#3869, and audits #3892/#3899/#3906 unchanged.

## H — hypothesis

With the compact hybrid, 700 updates, optimizer, authority gates and test suites fixed, replacing half of only the training CORRECT rows with declared near-boundary examples increases paired held-out shifted CORRECT accepted recall by at least 0.10 mean while preserving IID accuracy (≤0.02 paired drop). The treatment will clear the original shifted quality gates on all three fresh seeds.

## T — frozen treatment

- Allocation `needle-intent-distill-3458-pilot-08-stratified-correct`, seeds 3480–3482, additive path `research/system1/needle_distill_3458_pilot_08_stratified_correct/`.
- Per seed paired balanced control and stratified treatment. Same 6→16→16→3 tanh MLP, identical deterministic initial state, AdamW lr .008, batch size 64, 700 fixed minibatch updates, and identical minibatch-index RNG stream. Treatment retains 1,024 balanced CORRECT rows and adds 512 band-A plus 512 band-B rows.
- Both arms use 2,048 rows per class. Control uses all balanced rows. Treatment preserves all CONTINUE/WATCH data and exactly 1,024 balanced CORRECT rows, replacing the other 1,024 with a disjoint seed's near-boundary CORRECT rows (`abs(dx)` [.071,.149], `abs(dy)`≤.10, `abs(vx/vy)`≤.05, confidence [.80,1], visible=1). No architecture/capacity, optimizer, steps, threshold or hybrid change.
- Common held-out suites per seed: 1,024/class IID diagnostic, 1,024/class with only CORRECT shifted, 1,536 explicit boundary cases, five invalid metadata/envelope/nonfinite probes and 2,000 latency probes/arm. Preserve every six-float input, teacher label, both arm decisions, model state/digest and latency sample. Auditor independently regenerates rows, recomputes both predictions/metrics and paired contrasts without importing runner.py.
- Retain independent SHA-256 commitments to each arm's exact 6,144×6 training tensor, labels, initial weights and 700×64 minibatch-index stream. The auditor regenerates and checks these, as well as the evaluation data, before recomputing predictions from final weights.
- Construction tests cover the exact paired mixture, seed separation, six-dimensional bounds, teacher/gate logic, and minibatch-stream repeatability; no optimizer update during construction. Freeze sources, auditor, tests, seeds, image identity, command and hashes before the only formal container invocation.

## D — decision

`PASS_STRATIFIED_CORRECT_AUGMENTATION_SCOPED` iff all treatment seeds satisfy shifted accepted accuracy≥.95; per-class coverage≥.75 and accepted recall≥.95; false-CORRECT fraction≤.005; boundary/invalid YIELD; CPU p95<60 ms; IID accuracy≥.95; mean paired CORRECT recall lift≥.10; IID loss≤.02; and shifted CORRECT recall standard deviation≤.05. Scientific miss=FAIL; evidence defect=HOLD; environment/formal failure=STOP. One allocation, no retries/tuning/seed replacement.

## C — constraints

Local cached Docker CPU image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14 / PyTorch 2.5.1+cpu; network none, no pulls/prunes/cleanup, CPU only, read-only source/root and isolated writable output, 2 CPUs/4 GiB/64 pids/64 MiB tmpfs. No external model/API, real labels, GUI or execution authority.

## U — limits

One synthetic teacher, one train/test mixture, three paired seeds. This tests only whether this specific small Needle benefits from targeted coverage of the declared covariate shift. No Astra labels, real task effect, generalization claim, runtime/product safety, or execution authority.
