# WSLc execution environment

No image build was needed. The cached image was selected by immutable digest: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; WSLc image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`; Python 3.12.15; Linux/amd64. Candidate and independent auditor ran in separate WSLc containers with pull disabled, network disabled, source and input mounts read-only, one CPU and 512 MiB requested. The candidate output and audit output used separate writable mounts.

WSLc warned that swap-limit support/cgroup is unavailable. The memory cap was requested but is not claimed as enforced. No GPU was used: this deterministic 16-raster CPU fixture is too small to benefit from GPU transfer or execution overhead.
