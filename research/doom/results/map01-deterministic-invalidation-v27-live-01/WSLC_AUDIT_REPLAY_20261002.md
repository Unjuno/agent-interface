# WSLc replay of the retained v27 audit

## H / T / D / C / U

- **H:** Re-executing the frozen raw-only auditor in a network-disabled WSLc container will reproduce the retained v27 controller-composition disposition from the byte-identified source and raw archive.
- **T:** One posthoc auditor invocation against allocation `map01-deterministic-invalidation-v27-live-01`; the source directory was mounted read-only. The original live candidate was not launched.
- **D:** Exit code 0, `passed: true`, `RETAINED_DETERMINISTIC_COMPOSITION_PASS`; emitted audit fields and values matched the retained `audit.json`.
- **C:** This is a second-runtime audit replay of the same one-shot retained allocation, not a new live control comparison. The original allocation has one injected test event and no natural-change control.
- **U:** It confirms reproducibility of the retained audit in WSLc only. It does not show natural threat response, game progress, survival benefit, reliability, latency distribution, token savings, or MAP01 clear.

The original frozen allocation ran once and remains unchanged: one injected invalidation interrupted the first planner turn, the active cover released, the dependent answer was discarded with zero plan admissions, and a fresh second turn completed on the same planner thread. Three admitted programs had verified release. The run ended alive but unfinished, with no kills or exit. The retained audit records capture-to-detection 76.228 ms, detection-to-interrupt send 0.025 ms, interrupt send-to-ack 2.192 ms, interrupt send-to-completion 3.279 ms, and detection-to-cover release 24.057 ms.

The container replay used WSL 3.0.1.0 / kernel 6.18.40.1-1 and the already cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` image (image config ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Python 3.12.14). Network was disabled, source and raw inputs were mounted read-only, one CPU and 512 MiB were requested, and the container was removed on exit. WSLc printed: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Resource enforcement is therefore not claimed. No GPU or Docker was used; the hash/raw-JSON audit did not need GPU computation.

Source, preregistration, auditor, retained manifest, report, protocol, and existing audit identities are recorded in [the JSON receipt](WSLC_AUDIT_REPLAY_20261002.json). All 10 frozen source SHA-256 values matched before the invocation. The auditor verified 96 retained files totaling 6,472,270 bytes. No existing retained artifact was changed.

The current #59 live threat-control and natural MAP01 gates remain open. Do not rerun this consumed candidate allocation.
