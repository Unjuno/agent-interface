## PRE-FORMAL FREEZE — Issue #4485

Fresh allocation: `issue3924-orbstac-broker-contract-v2-20260926-01`.

- Intake main was `a718da028d33c9608433789676ddd7204d8c5d14`; immediately before freeze, current main and this branch are both `67f1aedace0039d2ab8e4550becfaea78c50653c`.
- Broker Git blob remains `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`, SHA-256 `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`; existing test blob remains `e645ae575cd6fdae02556df9facc9919739584f3`, SHA-256 `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`.
- Frozen local image: OrbStack 29.4.0 linux/arm64, Python image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- The exact dual-mount construction check passed: `/repo` and `/study` were both read-only; the fake path exists, is executable, and hash-matches; real Codex is absent. Formal cases=0, broker invocations=0, fake invocations=0.
- Allocation v2 will run the frozen seven cases once in a fresh network-none container, then the raw-only auditor once in a second equivalent container. A mount/source preflight executes before case 1. Any pre-case failure is STOP; the allocation is never rerun.

H/T/D/C/U and the preregistration digest are in `FREEZE.json`. This note preserves the exact current-main refresh before formal execution.
