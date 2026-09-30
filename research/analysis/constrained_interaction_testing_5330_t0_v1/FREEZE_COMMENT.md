# T0 freeze — Issue #5330

Allocation `constrained-interaction-5330-t0-20260930-01`, frozen on main `57b56de2831204885c55375737580e5d82d3ab98` before formal execution. H/T/D/C/U, exact factor levels and planted synthetic oracles, deterministic greedy covering algorithm/tie-break, strict pass/fail/STOP conditions, source hashes, command, and container identity are in `README.md` and `FREEZE.json`.

One isolated synthetic matrix only: four binary factors; 16 possible assignments; OFAT, pairwise, 3-way, and exhaustive controls. The pair oracle is the synthetic conjunction `freshness=1 AND lease=1`; the triple oracle is `freshness=1 AND responsibility=1 AND delivery=1`. They are design-sensitivity controls, not claims about real hazards or factor independence. No runtime, model, GUI, external action, network, or application fault injection.

Container: `python:3.12-slim`, image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, network disabled, root filesystem read-only, all capabilities dropped, no-new-privileges; source mounted read-only and only the previously absent output directory mounted writable. Python 3.12.14, standard library only.

Construction check (separate from formal): `python -B -m unittest -v research.analysis.constrained_interaction_testing_5330_t0_v1.test_design` — 7 tests passed. Derived design check: OFAT 5 rows, pairwise 6 rows/24 of 24 pairs, 3-way 8 rows/32 of 32 triples, exhaustive 16 rows. Formal command exactly once: `python -B -m research.analysis.constrained_interaction_testing_5330_t0_v1.run /out/formal-01`; only on zero exit, independent raw-only audit exactly once: `python -B -m research.analysis.constrained_interaction_testing_5330_t0_v1.audit /out/formal-01/raw.json`. No retries or changed oracles.

Source SHA-256: README `bb2e851667dd19fa79563caa419d8914cd94e874642766888a66dc9b0b65ea28`; design.py `23341c871b2ade675dbbc4e0749682902c6e8fc1405c58855ddf12574fd6b16e`; run.py `b772f8cee07350861d461faa99e9b91bda369945d582abd5bfd443802ad3aaa2`; audit.py `ca4688b1189e4d287601b89b7c2bf24d33904695fba60b5946e2a0735a3f55bf`; test_design.py `fc8b032e7d64dad4f773c6338564d5f132561926190e1263955c0431276e7b66`.

This rung can establish only that the declared deterministic designs cover the declared synthetic combinations and expose their deliberately planted finite oracles. It cannot establish production hazard coverage, useful interaction strength, real factor independence, or safety.
