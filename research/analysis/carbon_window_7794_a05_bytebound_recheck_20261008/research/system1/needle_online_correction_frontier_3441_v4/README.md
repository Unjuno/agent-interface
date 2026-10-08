# Issue #4834 — online correction frontier with disjoint evaluation data

This is a new allocation after the preflight STOP in #4829. It does not alter
the earlier frozen source, construction results, or STOP records. The key
protocol correction is that A-base training uses its own split; neither
held-out set is used for optimization or model selection.

## H/T/D/C/U

**H.** A shared rank-2 online correction adapter may acquire the opposing B
mapping while losing candidate-A competence, even when held-out A is disjoint
from A-base training and the untouched base remains an A fallback.

**T.** The frozen allocation uses seeds 65117, 65229, 65341; eight input
coordinates (coordinate 0 balanced binary, seven seeded continuous nuisance
coordinates); hidden-16 tanh; four outputs. A target is coordinate 0; B target
is its complement. Four separate fixed RNG streams per seed generate 256 A
training rows, 256 held-out A rows, 256 held-out B rows, and 256 balanced B
correction rows arranged as 32 unique batch-8 arrivals. The construction and
independent audit verify deterministic regeneration and exact row-level
disjointness across all four splits.

Train the A base for exactly 400 single-row AdamW updates (LR .03) on A-training
only, using the fixed index schedule (step*17+seed)%256. Freeze the base.
Initialize one rank-2 candidate adapter with an exactly zero second factor;
apply exactly one AdamW update (LR .04) per fixed balanced B minibatch. Measure
candidate A/B accuracy and cross-entropy at step 0 and after every arrival,
plus immutable-base A. The standalone raw-only auditor does not import the
trainer; it regenerates every split, checks all data identities, and recomputes
all per-row logits and metrics from retained base/adapter tensors.

The only formal environment is the cached local Docker image
needle-pilot05:local, exact ID
sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e,
linux/amd64, CPython 3.12.14, PyTorch 2.5.1+cpu, CPU, one thread, network none,
read-only source/root, 1 CPU, 2 GiB, 64 PIDs. No pull, install, GPU, retry,
replacement seed, tuning, host fallback, GUI, user data, or action authority.

**D.** Forgetting requires any seed's candidate B >=.90 while candidate A <.90
after an update, with independently verified base A >=.90 and valid evidence.
Scoped PASS requires final B >=.90 and every A checkpoint >=.90 on every seed,
plus exact data regeneration/disjointness, immutable base, exact independent
logit/metric reconstruction, guard/corruption controls, and zero audit errors.
Valid integrity with final B <.90 is no-acquisition FAIL; otherwise HOLD.
Source, data, image, environment, or audit defects are STOP, not model outcomes.
One formal trainer and one separate auditor invocation; no retry.

**C.** The opposing labels deliberately share one binary feature, so
interference is expected and the result is synthetic. The optimizer schedule
and thresholds are fixed; no hyperparameter claim or deployment inference.

**U.** No natural-language corrections, Astra demonstrations, vision, GUI/task
effects, generalization, realistic forgetting prevalence, concurrency,
durability, production latency/safety, routing cost, or action authority.

## Commands

Construction tests do not call the formal trainer or perform optimizer updates:

    python /src/test_needle_frontier.py

After freeze, exactly once run:

    python /src/needle_frontier_study.py --output /out/raw.json

Then in a second container with /out mounted read-only:

    python /src/needle_frontier_audit.py /out/raw.json --output /out/audit.json

See FREEZE.json for source checksums, intake main SHA, and formal invocation
policy. result/formal/ remains absent until the one frozen trainer invocation.
