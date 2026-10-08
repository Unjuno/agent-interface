# A02 freeze — fresh-seed support-rule sensitivity

Frozen before candidate/auditor invocation. This is not the formal six-case #6576 T0 allocation.

- Base main commit: `049cc5edb9e020ed31ce2bdc8f8dac45a93f53d8` (current `origin/main` when frozen).
- OrbStack VM: `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04 arm64. Outer cgroup as rechecked: CPU `200000 100000`, memory `4294967296`, swap `0`.
- Private Docker Engine: no running containers at freeze; prior A01 candidate/auditor containers are exited and belong to this task. Shared `unjuno-native-ci-6092` is out of scope.
- Image: `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, linux/arm64, already cached; no pull allowed.
- Candidate and auditor: network none; rootfs read-only; source/input and candidate raw output read-only for the auditor; distinct output mounts; 1 CPU; 2 GiB RAM; memory-swap 2 GiB (zero swap); `/tmp` tmpfs 64 MiB noexec/nosuid.
- Candidate max 1; independent auditor max 1 only if candidate exits 0; retries 0.
- Inputs: 90 deterministic fixtures, 30 seeds per arm, 4,000 observations each; frozen generator and `input.json` SHA below.

## Frozen SHA-256

| Artifact | SHA-256 |
|---|---|
| `PREREGISTRATION.md` | `61e8fc3e144718839c219fb6cb3b1e1bec8f850f804d85aca674a8ae6a4d2bb7` |
| `generate_input.py` | `6c4b6af10dda5d32fc7e3dda8c4ebecd107d9999c5b2c6ccaecb3a9eda0b45b9` |
| `candidate.py` | `7cacede5c740b3e363f23b152be6599fa4a45fdebe15d863518137312a19c22f` |
| `audit.py` | `53a60a25978503ebb5351cb5ed8306944c7859aebc11489c296c1acdd794c21a` |
| `input.json` | `ce0b0ee997407293e1639ef7acfe419a855dc2bb3206e5a08d5c924ad1d04aef` |

Only deterministic input generation, syntax compilation, hash computation, and preflight were done before freeze; no gate results were calculated.
