# #2558 OrbStack golden-v3 integration experiment

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: the golden-v3 doctor can be run from an OrbStack Linux container, but the frozen integrated route may still stop at its Windows/model boundary.
- T: execute `runtime/golden_desktop_demo_v3.py doctor` in a Docker container under the `orbstack` context, after resolving the import closure from main.
- D: main revision `14ca670c49d8b2144c4e0104d92526e394f0d02a`; container runtime reported Linux aarch64 on OrbStack, `DISPLAY=:99` passed, and the doctor returned `passed: false`. The route did not allocate a model call or GUI task. Missing boundary checks were `wslpath`, `windows_python`, `windows_cli`, `codex_cli`, and the Windows Node path was absent; the first minimal run also exposed that the golden import closure must include the research/live_control package rather than copied demo files.
- C: `STOP_DEPENDENCY_AND_MODEL_BOUNDARY`; no PASS/FAIL correctness or performance claim is made. This is an executed experiment and a stop, not a synthetic preflight.
- U: provide a verified model-boundary adapter or mount the complete supported host CLI, then rerun the frozen allocation unchanged.

## OrbStack provenance

- Docker context: `orbstack`
- Docker Server: 29.4.0
- Kernel: `Linux-7.0.14-orbstack-00380-ga7e0a2dc9535-aarch64`
- OrbStack: 2.2.3 (`c83556b0ef8f1ba9a33abbb194622b6b7a1c0307`)

The earlier #57 result remains immutable. This report records the actual container execution and its stop boundary for successor #2558.