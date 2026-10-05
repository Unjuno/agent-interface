# T0 execution receipt

Allocation: UNJUNO-7778-SLACK-RECLAMATION-T0-20261005-01

Frozen source, fixture, protocol, and construction-test hashes are recorded in
FREEZE.json. The three formal stages ran once each, sequentially, after the
freeze. All exited 0. No retry or replacement allocation was made.

Runtime:

    wslc 3.0.1.0
    python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
    Python 3.12.15, linux/amd64
    --pull never --network none --cpus 1 --memory 1g
    source mount: read-only
    output mount: separate writable formal_01/

    1. wslc run --rm --pull never --network none --cpus 1 --memory 1g
       -e OUTPUT_DIR=/out -v "${PWD}:/src:ro"
       -v "${PWD}\formal_01:/out" -w /src
       python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
       python -B generator.py
       exit 0; wrote 9 traces / 27 total jobs
       inputs.json SHA-256:
       1461d74889e1e40f216c99c7bf84cf5bd03636175f5c532b695d560412757abc

    2. wslc run --rm --pull never --network none --cpus 1 --memory 1g
       -e OUTPUT_DIR=/out -v "${PWD}:/src:ro"
       -v "${PWD}\formal_01:/out" -w /src
       python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
       python -B candidate.py
       exit 0; wrote 27 policy rows
       candidate.json SHA-256:
       8550758c00ae0346797c7544d39f4447529962dcafcc4e2b17a3e3ae0990a32c

    3. wslc run --rm --pull never --network none --cpus 1 --memory 1g
       -e OUTPUT_DIR=/out -v "${PWD}:/src:ro"
       -v "${PWD}\formal_01:/out" -w /src
       python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
       python -B auditor.py
       exit 0; PASS_METHOD_SCOPED / H_PASS_SCOPED; 0 audit errors
       audit.json SHA-256:
       39eb63f1a12e1034bd8bad7ee1a5466cbc1922fdf09598964015c2e7d2a29948

Each WSLc invocation printed:

    Your kernel does not support swap limit capabilities or the cgroup is not mounted.
    Memory limited without swap.

This warning is retained as an infrastructure limitation. The configured
1 GiB memory value is not treated as an effective cap. Candidate and auditor
ran in separate containers; the formal data exchange was the retained JSON
files in formal_01/.

The five construction tests passed before freeze. They were not rerun as part
of the formal allocation. The in-memory pre-freeze smoke result is explicitly
not treated as a formal result; only the frozen JSON outputs above determine
the scientific disposition.
