# T0 source and runtime freeze

Issue #6691 allocation `VERSION-DEFINED-6691-T0-20261002-01`.

- Initial intake main: `8c06589df01b2c4c1ab4017744faca61cab729f8`; refreshed base immediately before formal freeze: `c8e8bccd6dd96fda518111b526bd499582186566`. The fast-forward added no changes in this experiment's path; new `research/analysis/README.md`/`RESEARCH.md` entries were separately inspected.
- Branch: `research/version-defined-intervention-6691-orbstack-t0-20261002`.
- Candidate and audit source path: this directory; candidate and auditor execute once each.
- H/T/D/C/U and the B=off primary-estimand clarification: [PLAN.md](PLAN.md), preregistered on Issue #6691 before formal execution.
- Image: `python:3.12-slim-bookworm`, local RepoDigest `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, `linux/arm64`, Python `3.12.14`.
- Engine: OrbStack Docker Engine `29.4.0`, Linux `aarch64`, cgroup v2. `docker info` advertises memory/CPU/pids support; these flags are configuration requests, not proof of effective per-container enforcement. Host VM reports 10 CPUs and 16,819,609,600 bytes; macOS host reports 68,719,476,736 bytes. No task inference depends on performance/resource limits.
- Candidate and auditor containers: `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --cpus 0.25 --memory 256m --pids-limit 32`; source mounted read-only; dedicated output mount writable. No model, GUI, real application, user data, or live action.
- Construction: five local unit tests passed before freeze. The construction run is not the formal allocation.

## Frozen source SHA-256

```
1f2d9106ed540aad6c406a000e4f215e83db80b719968a6b30574f6b4a7eeec4  PLAN.md
1e12b565ef699b4af64e01c65d608e4675990c6074c13e298a37467cbb82ead8  candidate.py
0d16b3949dd780abf874699a419adebc2e3de2f7839024a4614a2e7ffc78f1ae  auditor.py
940e22bd56a991a336f479fc544bae9318073793af98acdb194bdc54b9503205  test_t0.py
```

Any mismatch before execution is STOP; do not repair and proceed under this allocation.
