# Construction record — Issue #7993 T0-A02

This package was constructed as a separate exact-enumeration successor to the finite-cohort A01 in PR #8028 and the exploratory repeated-cohort Monte Carlo artifact in PR #8034. It does not import, pool, or reuse either artifact's rows or results.

The registered estimand is the expectation of an uncapped inverse-probability weighted error-risk estimator under the declared superpopulation/outcome and resolution design. The truth-side outcome-error probabilities are `p_A=1/4` and `p_B=3/4`; resolution probabilities are `q_A=1/2` and `q_B=1`. The public candidate input omits the truth probabilities and unresolved outcomes. The builder enumerates four binary outcomes and two resolution indicators (64 joint states). The auditor independently reconstructs the exact weights, support, estimator expectation, and design risk. A zero-support control must return `UNKNOWN_NONPOSITIVITY` without a numeric estimate. Six output mutations are required to be rejected.

Construction checks only (no formal candidate CLI or auditor CLI invocation has occurred):

- `python3 -m unittest -v test_construction.py`
- `python3 -O -m unittest -v test_construction.py`
- `python3 -m py_compile build_fixture.py candidate.py audit.py run_formal.py test_construction.py`
- `nice -n 10 python3 -B build_fixture.py` to regenerate the deterministic public and auditor fixtures.

The execution environment is native macOS arm64 with CPython 3.14.5. An OrbStack image-store read failed during read-only image inventory with `operation not supported`; no image pull, container creation/start, prune, or service restart was attempted. The formal allocation, if the preregistration gate is met, is a single sequential low-priority host run. No container, network isolation, or product/live-authority claim is made.
