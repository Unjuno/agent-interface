# A01 freeze — timer quantization and eligibility diagnostics

Frozen before candidate/auditor invocation. Formal #6576 six-case T0 allocation is untouched.

- Base main commit: `dbf0056e96ae1a3b04fe426cb86501442661a1b8` (observed `origin/main` at branch creation).
- Dedicated OrbStack VM: `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04 arm64. Outer cgroup: CPU `200000 100000`, memory `4294967296`, swap `0`.
- Private Docker daemon in that VM: daemon present; pre-run `docker ps` empty. Shared host daemon `unjuno-native-ci-6092` not used.
- Candidate/auditor image: `python:3.12-slim`, linux/arm64, local image digest `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (no pull permitted).
- Container controls: network none; root filesystem read-only; source and input mounts read-only; separate initially absent output mount writable; 1 CPU; memory 2 GiB; memory-swap 2 GiB (zero swap); `/tmp` tmpfs 64 MiB, noexec/nosuid.
- Candidate invocations allowed: 1. Independent auditor allowed: 1 only after candidate exit 0. Retries: 0.
- Cases/seed/counts: `continuous` q=0, `quantum_025` q=0.25, `quantum_100` q=1.0; seed base 65761111; 4,000 train and 10,000 heldout per arm.

## Frozen SHA-256

| Artifact | SHA-256 |
|---|---|
| `PREREGISTRATION.md` | `6e1b6cf9ea730f9f85d32be6f01aed9abf659ce082f6e09d3c93b1fe6755e565` |
| `generate_input.py` | `02407b7bc807f2651680e2d661f458170b83fb09f529870b6f1a13e4f73261e9` |
| `candidate.py` | `71ddb1086bfa34ef576d44c6c0b0971e876ff8ec326766b92c7d41c4191e1006` |
| `audit.py` | `95b380ba42215e4671012b0ac5186588e1a090c79089d7f59d70899fcf3e555c` |
| `input.json` | `0f051552ce2fa4235d65806a5e59df8af6177d94d802b885962703f1206f63a7` |

No fit, audit, or result calculation was run during construction. `py_compile`, input generation, source hashing, and diff checks are preflight only.
