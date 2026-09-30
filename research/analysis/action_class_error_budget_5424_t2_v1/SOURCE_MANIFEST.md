# Source and raw manifest

Frozen base `main`: `5a741e5fe4d427a560c21975b8a0b693fb48fd66`.

Formal experiment source commit: `24cfb823d3ac0b2c30e5d353d76543a7198a2c90`.

| File | SHA-256 |
|---|---|
| `PLAN.md` | `50e08b982d2eda05be7117fd85f81cdabf8a6193a3c1c40b9a38b65fa4e7011d` |
| `experiment.py` | `d08c95b17e39d8f04ec2a21bf7d25f78cec9b51f8c95494a37b7e4c9f081884f` |
| `audit.py` (v1, retained FAIL) | `db8d3c7a1029e5023a04cd6e7de2bd8d5bd0e830293b1193305be7b44c61a073` |
| `audit_v2.py` (summary-only correction) | `042d0ccfbfaa8cd19d0ff85dfeab6b6a5fbcf3ce57035f7d54749a598cff82a3` |
| `AUDIT_REPAIR.md` | `85ffedb03ef1c29a01253832092cb7a477a9f39fd3fb564c38aebda2b6edc923` |

Container image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; local image ID is the same digest, Linux/arm64. OrbStack Docker server `29.4.0 linux/aarch64`.

Formal raw hashes:

| File | SHA-256 |
|---|---|
| `raw/formal/inputs.jsonl` | `cdc4ef16c30ec667c0cd043d1d69e2625b36fba4d14a3c50e27245c2e9330e8b` |
| `raw/formal/outcomes.jsonl` | `102896d62c357701d146b942003c650e73b6900bec36a7c1ecfe9d43b5e9ad48` |
| `raw/formal/summary.json` | `9348e3aea0eed2fd3ca4e3949763c6ab3d44d3af5d5638e25c7e753a56d740c8` |
| `raw/formal/audit.json` (v1 FAIL, preserved) | `e100bd96f2e7d6de7effa1d60e7b7756d0aa5df775c35cda31c14e2b8cb8e346` |
| `raw/formal/audit_v2.json` | `a9ae407f62918b2dfddefe519a143a70cd3acccba2a4fc7229715df98ffcd5c1` |
