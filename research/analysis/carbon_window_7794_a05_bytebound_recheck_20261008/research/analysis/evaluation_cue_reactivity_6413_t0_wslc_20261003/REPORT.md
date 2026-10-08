# Issue #6413 T0 — evaluation-cue construction audit

**Disposition: `METHOD_PASS_SCOPED` for static synthetic construction only.** A separate raw-only auditor reconstructed 12 valid task renderings, six cue-pairs, and all three planted invalid controls. This is not a model-behavior or evaluation-awareness result.

## H / T / D / C / U

- **H:** This T0 does not test the behavioral hypothesis. It tests the prerequisite construction claim that an evaluation-context label can be varied independently of the fixed task contract within two objective-salience levels.
- **T:** Three #4695 v2 held-out positive panels × two cues (`EVALUATION`, `DEPLOYMENT`) × two objective-font levels (12 px, 24 px), plus three invalid controls. Source and hidden target truth are bound to the original manifest SHA-256 `bf1410efd3f34963d95cfe6578a6fb272e760ec528b77083956c1965556b37ee`. Candidate and auditor were separate images and containers. WSLc 3.0.1.0, Arch Linux/WSL2, cached CPython 3.12.15 linux/amd64 base, network disabled, no image pulls, one CPU requested. Construction tests: 7/7.
- **D:** `METHOD_PASS_SCOPED`: 12 valid rows reconstructed, all six within-salience cue pairs differed only in cue text, no auditor errors, and the invalid controls were classified `CONFOUNDED_TARGET_VISIBILITY`, `AUTHORITY_CHANGED`, and `CONFOUNDED_REALISM_EDIT`. Candidate exited 0 once; independent auditor exited 0 once. No retries.
- **C:** Synthetic high-contrast orange-square panels; static SVG text is a presentation proxy. Exposure is metadata only and font rasterization was not rendered/measured. Cue-label attention may itself vary.
- **U:** No model, GUI, route, action, live effect, human participant, task success, hidden model recognition, strategic intent, transfer, causal awareness, or safety claim. A T0 PASS only establishes this narrowly specified synthetic construction gate; it does not authorize T1.

## Formal result

Independent audit output: `METHOD_PASS_SCOPED`; 12/12 valid rows; 6/6 cue pairs; four source-manifest panels reverified; zero errors. The target-absent substitution, observe-only tool change, and offscreen objective were separately detected with the preregistered classifications.

- Candidate: one WSLc invocation, exit 0; 79,408-byte raw output, SHA-256 `8ce339f94814436e4bf11cc0b9dbcd1f0ea9db7c921a993c6dc31c4522fac3a9`.
- Auditor: one independent WSLc invocation, exit 0; 340-byte audit output, SHA-256 `a65c3a4bba837347b979fa72a2cabcc590ea685e63f3fbe4747ba820a45c1f61`.
- Candidate image ID: `sha256:0ce236142180bbb3d146f3e546a60b5091a771786ee0511501f8d6fb5540aef3`. It contains no source manifest, target boxes, oracle fixture, auditor, or tests.
- Auditor image ID: `sha256:41d5cb7cd70c3f09d46811ec5ce22f26aca4a144bd887dce54b7c288bd3254e4`; it contains frozen raw evidence and source-derived oracle, but no candidate code.
- Freeze: [`FREEZE.json`](FREEZE.json); preregistration: [`PREREGISTRATION.md`](PREREGISTRATION.md); exact invocations and environment: [`RUN_RECORD.md`](RUN_RECORD.md); immutable raw and audit outputs: [`results/formal-a01/`](results/formal-a01/); digests: [`SHA256SUMS`](SHA256SUMS).

WSLc exposes no read-only-rootfs, capability-drop, or no-new-privileges flags. Source/input/evidence files were made non-writable and the process ran as UID 65532; no hard memory-enforcement claim is made. The formal images used the cached pinned Python base, `--pull never`, and `--network none`. No GPU was used because this deterministic fixture/audit is CPU-only.
