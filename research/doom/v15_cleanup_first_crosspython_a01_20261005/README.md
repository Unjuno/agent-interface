# V15 cleanup-first cross-runtime regression — bounded STOP

This package records one normal and one optimized execution of the predeclared seven-module fake-X regression suite from the exact virtual merge tree of current main and PR #8094. The result is an environment STOP: the cached minimal Python image lacks Pillow, which eight methods need through the tested wrapper import chain. No code-level test conclusion is assigned to the incomplete suite.

## H/T/D/C/U

- **H:** The exact current-main + #8094 virtual-merge source tree preserves cleanup-first per-key identity and finite handback in its bounded regression suite under a pinned Linux CPython runtime.
- **T:** One normal and one optimized Python invocation of the seven test-module groups in RUN_PLAN.json, source tree 2ce07e058ed6b868ea97799e9a7b65deff21da71.
- **D:** Both invocations discovered 47 tests and exited 1 with 8 import errors each. Every recorded error is ModuleNotFoundError: No module named 'PIL'; WSLc emitted a cgroup/swap warning. Disposition: STOP_CONTAINER_IMAGE_MISSING_PIL, not candidate FAIL and not PASS. No retry occurred.
- **C:** WSLc 3.0.1; Linux/amd64 python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016, CPython 3.12.15; network and pull disabled, one CPU, 512 MiB requested, read-only source mount, --rm. The memory request is not claimed as enforced.
- **U:** The import errors leave the synthetic regression gate unresolved. This does not establish native X11, threat response, physical input, game/application consumption, useful feedback, recovery efficacy, latency, gameplay, or Issue #59 completion.

## Raw data and audit

The four *.stdout.txt.b64 and *.stderr.txt.b64 files are base64 encodings of byte-for-byte captured WSLc streams. EXECUTION.json records each original byte count and SHA-256. The independent audit decodes/checks the streams and verifies all 1,996 extracted Python source files against SOURCE_MANIFEST.json without importing or executing candidate code.

The first pre-run extractor failure is retained in PREPARE_STOP_01.json. Do not rerun the two STOPped candidate commands. Any future dependency-qualified test must be a newly frozen successor and retain this STOP unchanged.