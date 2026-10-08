# ViZDoom clock-function symbol-to-runtime comparison — construction only

Disposition: `HOLD_BINARY_CODE_IDENTITY_NOT_ESTABLISHED`. No engine breakpoint was attached and no scientific/formal row was produced.

## H / question

Can an unmodified ViZDoom 1.3.0 source build with a linker map provide a `VIZ_Tic` PC that can safely be used to attach a kernel hardware execution breakpoint to the pinned wheel engine, without instrumenting or replacing the runtime under measurement?

## T / build and comparison

- Offline OrbStack Docker build using local image `agent-interface-map01-clock-counter-v1:20260920` (`sha256:fdf45a138d5b025499f6808ae0b8a04a12d2ad4643e6618f913a85e1cfe64e17`). Source HEAD `c8e0a31182d98c6f40a65674283e736b851e8e59`; a detached clean worktree was built, leaving the image's separate instrumentation change outside the baseline worktree.
- Debian GCC 12.2.0, CMake 3.25.1; Release flags `-O3 -DNDEBUG -g`. Linker map only (`-Wl,-Map=...`); no runtime patch in the baseline source.
- Baseline `vizdoom` executable SHA-256 `df948feffe93a27345f02eec891f85d89841a927c6062999b9a42a84f0db40b2`; its map resolved `VIZ_Tic()` to link address `0x3eee80` (relative `.text` offset `0x33c080`).
- Compared the baseline against the exact executable in pinned fixture image `issue-3300-map01-fixture-smoke:v2`, ID `sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca`, executable SHA-256 `355235742626ed6152fa2ba8c2ddf82e03003b42033aa3d16baf22cbd317ec11`.

## D / result

The binary `.text` sections are not byte-identical: baseline size/hash `3,967,568 / 757e0be2d40a63287247e5f5d404152b5948335ba972356537817fa251f90f54`; pinned runtime size/hash `4,022,632 / 7ca826f33026802009b0b0e35e0fa00de9cc06451202e805e84e7443e261b17f`. The first 4, 8, 12, 16, 20, 24, 32, 48, 64, and 128 bytes at the symbol-bearing baseline `VIZ_Tic` location were each absent from the runtime `.text` (`find=-1`). Therefore the link-map address cannot be transferred to the wheel executable. Do not attach a breakpoint at `0x3eee80` in the pinned runtime.

## C / scope and interpretation

This demonstrates symbol resolution in a clean source build but fails the required code-identity bridge to the tested wheel. It does not show that `CAP_PERFMON` cannot support hardware breakpoints, and does not show that the runtime lacks a `VIZ_Tic` function; only the address transfer is unproven. No source instrumentation, gameplay action, phase sample, or clock claim resulted.

## U / next gate

Either obtain a matching debug-symbol artifact/build ID for the exact pinned runtime and prove PC-to-runtime identity, or use a different independent witness. A future candidate must compare exact machine code at the target PC before attaching one breakpoint, then verify event counts/timestamps and perturbation on excluded sessions. Formal collection remains 0/120 and #3453 remains `HOLD_LIVE_SPAN_UNIDENTIFIED`.

## Reproduction evidence

- `comparison.json` is the stdlib ELF section and prefix comparison output; SHA-256 `6e91f7ae7896cc32142f0650647d1520f0aa1a61f1e78d320fb2b7c40f90b380`.
- `compare_vizdoom_symbol_build.py` SHA-256 `1f83c2a97c7b5557c059eebb0ca1cff7274a382ae192694f8c6b1391bdba79c5`.
- `configure.log` SHA-256 `c10488c8cc96f2e4fe009f77a09cbca822296ee246a05e791c8ee74c3026f56a`; `build.log` SHA-256 `1ce01336cb7aa399bdf7a7a721348776a25d8fd5f0db82a1c29ad798dee5f57b`.
- Full linker-map SHA-256 `add5dca83f2be7669f5d5a350fbbab97097e8a616aa4b64f07c6598e88e2b057`; extracted `VIZ_Tic()` address is retained above. The baseline executable SHA-256 is retained above; the binary itself is not committed.
