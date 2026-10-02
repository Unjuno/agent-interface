# T3 formal run receipt

Allocation: `EFFECT-INTERFERENCE-5366-T3-20261002-01`.

Main base and pre-run source hashes are recorded in `FREEZE.json`. Construction history is in `CONSTRUCTION_LOG.md`. Formal candidate: one invocation only. If it exits 0, independent raw-only auditor: one invocation only. Retries=0. Any failure is terminal and preserved.

Candidate: `python3 candidate.py fixture.json outputs/formal/candidate_raw.json` — invocation 1/1, exit 0, 12 rows. Raw SHA-256: `b93ec4f2635920eded3758325fed095cb2e4980937e94795b4609cfde9a929ed`.

Independent raw-only audit: `python3 audit.py fixture.json outputs/formal/candidate_raw.json outputs/formal/audit.json` — invocation 1/1, exit 0, `PASS_METHOD_SCOPED`, 12 rows reconstructed, errors `[]`. Audit SHA-256: `129f5add800c68904770bdeabc58536f7587b3bb930029688c91d14412bd7a94`.

Retries=0; no formal source or raw output was changed after invocation. Freeze SHA-256: `44c44cb3bcfc17c9a70f3a4e942d5d7bf61f08ba12ccdb6a78e55db6e42b175d`.

Runtime: CPython 3.14.5, macOS arm64, standard library. No container/Engine, GUI, model, network, GPU, or OS input. No shared resource or existing container was touched.

Local CI equivalents passed after integration rebase to main `93f0ee168051d4b4afcf381ea8e88245d89448f5`: analysis index 376/376; focused T3 construction 5/5; analysis-index workflow suites 8/8 and 12/12; workspace-index tests 21/21 and 154 reachable directories; public navigation 26 documents / 1,233 links; Python compilation; whitespace/diff check. Hosted Actions are separate and are not represented as PASS here.
