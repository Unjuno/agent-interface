# Construction validation

Scope: Procedural Operations Facility v0 benchmark mechanics, determinism, controller boundary and instrument throughput. This file does **not** claim Agent Interface performance.

## Local construction evidence

Environment: current ChatGPT Linux execution container, Python 3.13.5, GCC toolchain.

- C11 build with `-O2 -Wall -Wextra -Werror -pedantic`: PASS.
- Python construction suite: **9/9 PASS**.
- C core positive/negative controls: PASS.
- committed fixed allocation: **12 seeds**.
- hidden-oracle reachability sweep: **12 seeds × 3 difficulty levels = 36/36 PASS**.
- same seed/config → identical specification hash: PASS.
- different seed → different specification hash: PASS in construction control.
- same fixed seed → byte-identical rendered PPM snapshot across repeated runs: PASS.
- controller-visible stdio state contains only `schema/tick/done`; seed, spec hash, hidden code and terminal truth are absent: PASS.
- invalid difficulty overrides fail closed without mutating the prior valid config: PASS.
- one-axis override isolation (`watcher_count`) changes only that report field: PASS.
- negative controls include premature watcher acknowledgement, missed watcher semantics, wrong code submit and assembly placement miss: PASS.
- fixed-seed paired harness verifies byte-equivalent episode identity for both arms after execution while controllers receive no seed/spec hash: PASS.

## Local seeded instrument performance

On this construction container, a diagnostic run at seed `424242`, difficulty `0.6` produced approximately:

- >5,000 hidden-oracle mechanics episodes/s in the 200-episode local smoke;
- >10,000 software-render frames/s for the 320×180 raycaster.

The automated performance test intentionally uses much looser non-regression floors (`>100 episodes/s`, `>500 render frames/s`) to avoid treating host variance as a scientific result.

These figures are benchmark-instrument throughput only. They do not measure a model or Agent Interface candidate.

## Fixed seed versus formal evaluation

The committed seed set exists so benchmark changes can be tested without human operation and replayed exactly.

It is suitable for:

- construction testing;
- deterministic debugging;
- CI regression;
- before/after benchmark-engine performance checks.

It is **not sufficient for a general capability claim**. Formal B0/C1 evaluation should freeze both controllers first, then generate fresh hidden paired seeds and reveal them only after the scored allocation.

## Container validation gate

The Dockerfile runs the fixed-seed test suite and performance smoke during image build. Repository CI should additionally build the final runtime image and execute at least one fixed-seed oracle episode and one paired-harness protocol smoke inside that image.
