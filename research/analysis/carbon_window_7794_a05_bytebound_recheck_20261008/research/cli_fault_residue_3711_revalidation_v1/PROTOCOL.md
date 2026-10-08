# Issue #3711 report-temp fault revalidation v1

Status: unchanged tests re-anchored on current main before the first CI execution of this candidate. Historical v1 protocol and outcomes remain unchanged.

## H / T / D / C / U

**H.** The frozen partial-write and report-fsync fault cases leave a visible `.report.json.tmp`, no final report, `unknown_or_incomplete`, replay disabled, and byte-stable read-only status inspection; successful publication leaves no temp residue.

**T.** Base commit `07858c6961fd4f2bea03fe33469817eab684780c`. Baseline test blob `0aebdb6e3033a1a05ea56b2847194a0ef3b225de`; current implementation `runtime/cli_v1/attempt.py` blob `70cc62b450c8b9c8aaa0db49b1e116388368fe4c`. The three test methods are copied unchanged from the #3735 candidate patch (source candidate commit `8193f3d25e6a9354d41d379792cab5e1351b1d54`, patch blob `ca6a77e0fd16328495ed5da9cab6dcab7b8bd917`); the merged test file blob is `4be661be8c0a405ded6c5e11f057723b20fa7b8d`. They are run once by the existing Runtime CLI workflow on this current-main-based successor branch. #3737's two overlapping cases are included; do not merge both branches.

**D.** Scoped PASS only if all three unchanged methods and the full Runtime CLI workflow pass on Ubuntu, Windows, and macOS for this exact successor head. Any test assertion failure is FAIL; workflow/runner/setup failure is STOP; incomplete matrix is HOLD. Earlier #3735 outcomes remain immutable and are not pooled as this candidate's result.

**C.** No GUI/model/input/network workload. The requested local Docker fallback is unavailable on this PC (C: has no free bytes and the Linux engine is unavailable); do not repair or clean the host. CI is explicitly remote execution, not a Docker claim.

**U.** Finite process-level injected write/fsync faults and one successful publication control only; no power-loss durability, arbitrary filesystems, full #3711 adoption, or product reliability claim.
