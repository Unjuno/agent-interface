# A03 freeze — quantization support-cutoff sweep

Frozen before candidate/auditor invocation; separate from formal #6576 T0.

- Base main commit: `aa0311f4501be749c117cbc3c73e5bd3f13bf744`.
- OrbStack VM: `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04 arm64. Outer cgroup: CPU `200000 100000`, memory `4294967296`, swap `0`.
- Private Docker Engine: dedicated to the #6576 VM; no shared native-CI Engine use.
- Image: `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, linux/arm64, cached; no pull allowed.
- Both containers: network none, read-only root/source/input, separated output mounts, 1 CPU, 2 GiB memory, memory-swap 2 GiB (zero swap), `/tmp` tmpfs 64 MiB noexec/nosuid. Inspect configuration before start.
- Candidate max 1; auditor max 1 iff candidate exit 0; retries 0.
- 200 fixtures (50/arm), 4,000 observations each; 800,000 observations total.

## Frozen SHA-256

| Artifact | SHA-256 |
|---|---|
| `PREREGISTRATION.md` | `3dfcdf5222d00fd548f0d21fe1a27b8762f3c0f3530a4f15a2ac62166803b12d` |
| `generate_input.py` | `da7cd467ee9a6b397ee367ba0f04e899b15ec65b5b159fb312176bf29ac86b73` |
| `candidate.py` | `228c73629a266af722c152358d3a6d51a21394cb1191095b2c5ea15849e16185` |
| `audit.py` | `7fb6165b07480f35ef320e94bf098ac9ed308a37e6e858b0dd349ee850d98852` |
| `input.json` | `2802756348963c0c5d71edab270c7d09c781e298ad371ffdfbe3f40e36be4685` |

Only deterministic input generation, syntax compilation, hashes, and environment inventory were run before freeze; no cutoff outcomes were calculated.
