# Issue #4847 CUDA construction allocation STOP

Allocation: \`tiny-visual-extent-readout-4817-cuda-20260927-02\`
Branch: \`research/tiny-visual-extent-readout-4817-cuda-20260927-v2\`
Frozen source commit: \`a21aa148795fcaa26edd72d11db055a621859ca7\`
Freeze blob: \`74e07a230fa37a8198ad8221f33b2ae7b6494408\`

## H / T / D / C / U

**H.** Test whether the #4837 fixed-seed extent-readout construction can execute deterministically on the pinned local CUDA image; no quality or GPU-benefit inference from setup alone.

**T.** One container invocation on cached image \`sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067\` (linux/amd64), with \`--pull never --gpus all --network none --read-only --cpus=1 --memory=2g --pids-limit=64\`, read-only source mount, fresh output mount, and container environment \`CUBLAS_WORKSPACE_CONFIG=:4096:8\`. Source and auditor blob IDs are in FREEZE.json.

**Observed.** Image identity matched. Before-run GPU snapshot was captured (local file hash \`FA208789B8178CFA07881CE74BF8195A865770E6B218A7B5CEC59F3ED8A6544B\`). The run passed its CUBLAS environment assertion and entered the strict deterministic CUDA probe. It exited 1 in \`finite_difference_probe()\` before dataset generation, either fit, or optimizer update: PyTorch rejected in-place perturbation of a leaf Variable requiring grad. No RAW.json was produced.

**D.** \`STOP_FINITE_DIFFERENCE_PROBE_IMPLEMENTATION\`. Independent post-stop checks: exit=1, expected leaf-variable error present, pinned image identity present, RAW.json absent, and fit/update counts all zero. Result: \`PASS_STOP_EVIDENCE_INTEGRITY\`. This does not evaluate the pooling hypothesis.

**C.** The prior #4846 STOP was a missing container environment variable. This new allocation corrected that boundary and exposed a distinct finite-difference harness defect. No retry, code repair, package install, or image substitution occurred in this consumed allocation.

**U.** The 49-point diagnostic did not complete; zero train/base/held-out data were materialized; max-only and max+mean fits are unrun. The scientific construction hypothesis remains unresolved.

## Retained evidence

- \`runner.stderr.log\`: SHA-256 \`8AAE62024763E642B3B381267FBCE6D8CF5DAA092ACB15E09C8A29E609E6EF25\`
- \`runner.stdout.log\`: empty; SHA-256 \`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855\`
- \`runner.exit\`: SHA-256 \`F1B2F662800122BED0FF255693DF89C4487FBDCF453D3524A42D4EC20C3D9C04\`
- \`image.txt\`: SHA-256 \`E5E19BD80C16E88AFAE7D9A7A31C26594323C7AB19036A0BDE48C7955694FB9B\`
- \`STOP_AUDIT.json\`: SHA-256 \`C40C67163C7AA39F4714FE10B623F729B0D61D4770604129B10C929E9649B80C\`
- Local full XML GPU snapshot: \`C:\Users\junny\AppData\Local\Temp\aiface-4847-cuda-v2\out\gpu-before.xml\`. The snapshot is retained on this PC; the compact auditable STOP artifacts above are committed here.

No formal fitting, training result, task-quality result, or adoption claim is made.