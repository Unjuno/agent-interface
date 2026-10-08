# #5008 v2 construction-gate STOP

Allocation: `needle-role-skill-lifecycle-4916-v2-20260928-01`  
Base main at evidence publication: `f4cbbd039db4d0b565e8d841a47d3b191b3a572c`.  
Disposition: `STOP_CONSTRUCTION_PARITY`  
Formal timing invocation: **not run** (preregistered parity gate failed).

## Frozen inputs and transport check

- Main ref observed before local work: `7e290a61d48d2b7810db042e19409f8fc49672b1`.
- Artifact: `research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json`; Git blob `45b80150dac503f4eb6f3cb5d82f9afa2c587107`; SHA-256 `2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a`.
- Expected fixture: sibling `builder/expected.json`; Git blob `d1f982ecb142c1d6f59962b6b777615b8f1544b2`; SHA-256 `5baca462abbcdd561db4ac790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61`.
- Both files were mounted read-only into cached image `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` (`linux/amd64`), with `--network none --pull=never --cpus=0.25 --memory=512m --pids-limit=32 --read-only`. Container-observed byte lengths and SHA-256 matched host values.
- The package's declared `payload_sha256` is the canonical SHA-256 of the full parsed top-level object after removing `payload_sha256`, matching the retained validator convention; it is not the digest of `tensors` alone.

## Construction parity result

Independent pure-Python implementation: [preflight.py](./preflight.py). It uses scalar linear layers, `math.tanh`, and the stored rank-2 residual `h @ a @ b / 2`, then compares argmax classes with all retained expected labels.

| Role | Rows | Matches | Mismatches |
| --- | ---: | ---: | ---: |
| A | 4,096 | 3,963 | 133 |
| B | 4,096 | 3,699 | 397 |
| C | 4,096 | 3,802 | 294 |
| Total | 12,288 | 11,464 | 824 |

Docker preflight output is preserved at [formal-attempt/stdout.json](./formal-attempt/stdout.json); process exit code was `2` (the script's typed STOP exit). The implementation was run once under the exact cached image and resource restrictions, using the frozen files. No timings, schedule, or performance summary were produced. No retry, altered scorer, row filtering, or package substitution was performed.

The preregistered construction gate requires 12,288/12,288 exact matches. Its failure terminates this allocation before the formal timing invocation. This is an integrity/implementation-precondition STOP, not evidence for or against lifecycle amortization. The upstream fixture's historical `load1/loader.json` records its own predictions, but those are not substituted for the preregistered pure-Python scorer gate.

## H / T / D / C / U disposition

- **H:** Not tested; no lifecycle timings were collected.
- **T:** Exact allocation and inputs above; only the preregistered construction-parity check ran.
- **D:** `STOP_CONSTRUCTION_PARITY`: 11,464/12,288; required 12,288/12,288.
- **C:** The scalar scorer is framework-independent, and may differ in floating-point rounding near argmax ties from the original PyTorch 2.5.1 CPU scorer. This possible numerical explanation does not waive the exact parity condition.
- **U:** No formal timing result, no evidence about lifecycle speed, no PyTorch-versus-Python performance comparison, and no product/runtime claim.

## Reproduction

From repository root on Docker Desktop with the stated image cached, bind this directory as `/inputs` read-only and invoke:

```powershell
docker run --rm --pull=never --network none --cpus=0.25 --memory=512m --pids-limit=32 --read-only `
  --mount "type=bind,source=<absolute-path-to-this-directory>,target=/inputs,readonly" `
  sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 `
  python /inputs/preflight.py /inputs
```
