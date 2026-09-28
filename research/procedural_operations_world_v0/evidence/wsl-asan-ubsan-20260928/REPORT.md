# WSL2 ASan/UBSan construction check

Issue: [#5206](https://github.com/Unjuno/agent-interface/issues/5206)
Allocation: `opsworld-5206-wsl-asan-20260928`
Execution checkout: `research/procedural-opsworld-5206-wsl-main-20260928`
Exact tested main: `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`
GitHub evidence branch: `research/procedural-opsworld-5206-sanitizer-20260928`

## H / T / D / C / U

**H.** The current-main validity-hardening C test suite, including its 10,000-seed feasibility and target-uniqueness loops, high-concurrency generation, and large event-ledger case, completes without AddressSanitizer or UndefinedBehaviorSanitizer diagnostics on this WSL2 host.

**T.** One compile-and-run from `research/procedural_operations_world_v0` on the exact main above. Host: WSL2 Arch Linux; kernel `6.6.114.1-microsoft-standard-WSL2`; GCC `16.1.1 20260430`. Preregistration: [Issue comment #5864664754](https://github.com/Unjuno/agent-interface/issues/5206#issuecomment-5864664754).

```sh
cc -O1 -g -std=c11 -Wall -Wextra -Wpedantic -fsanitize=address,undefined -fno-omit-frame-pointer -I. test_ops_world.c ops_world.c -lm -o /tmp/opsworld-5206-sanitized-test &&
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/opsworld-5206-sanitized-test
```

No retry, source edit, seed substitution, or parameter tuning.

**D.** `PASS_SANITIZER_COVERAGE_ONLY`: command output was exactly `20/20 validity-hardening tests PASS`, with no compiler warning or sanitizer diagnostic in the captured output. The test program prints this line after invoking all tests and immediately returns 0. The separately performed source census found 20 `static void test_*` definitions and 20 test invocations from `main`, matching the printed counter.

Raw stdout (complete):

```text
20/20 validity-hardening tests PASS
```

Source blob identities from the tested commit:

| Path | Git blob |
|---|---|
| `research/procedural_operations_world_v0/test_ops_world.c` | `f369fb7b76db2b7761ae431598133aa39571e0fa` |
| `research/procedural_operations_world_v0/ops_world.c` | `93e0cb129cff9eccefdd0aa9aa7c7f05ea407453` |
| `ops_world_part_00.inc` | `9bf195cebd4de73e348af071091a49fb4a835f64` |
| `ops_world_part_01.inc` | `118db3d10fbb20e28cce61eda231bea47173dbcd` |
| `ops_world_part_02.inc` | `8e3396329ada48a1e49a11d952b4d96798dc5e0b` |
| `ops_world_part_03.inc` | `5a29fedbe547dfbd9c255866e21f91f3f92bf078` |

**C.** Local WSL2 only; no container image was used because the shared Docker lane has no assignment for this work. No Docker invocation, model load, CUDA operation, GPU compute, fit, adapter write, GUI, or X-server path. The RTX 3080 was seen only in a separate read-only `nvidia-smi` inventory, which is not a lease. Existing test fixtures include deterministic seed sweeps; these are not formal experiment allocation seeds.

**U.** This checks only the paths exercised by the project-authored 20-test suite under one compiler/runtime. The source census is a structural consistency check, not an independent correctness oracle for each assertion. There was no independent raw-result auditor or durable sanitizer binary/stdout file; only the exact one-line stdout was captured and retained here. This is not a formal benchmark result, full validity proof, Xvfb/render validation, GPU/model result, or product claim.

## Scope boundary

This evidence is construction-only and does not promote Procedural Operations World to a formal benchmark. Follow Issue #5206's repair/revalidation gates for any discovered defect. The separate #5139 GPU fine-tuning allocation remains unstarted until its exact coordinator lease and all issue-specific freeze/preflight/attribution gates are satisfied.
