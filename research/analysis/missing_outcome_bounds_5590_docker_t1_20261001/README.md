# Issue #5590 — Docker T1 finite-cohort bounds reproduction

Fresh container-portability allocation following host-only T0 and a separately consumed OrbStack preflight STOP. The candidate, ledger, auditor and construction tests are unchanged from the host T0 and SHA-pinned in this directory. The one-shot Docker attempt ended in a preserved output-mount STOP; see [FORMAL_FAILURE.md](FORMAL_FAILURE.md). No real cohort or promotion claim is implied.

See [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json), and [SHA256SUMS.txt](SHA256SUMS.txt). Exact runtime evidence is retained in `results/docker-t1-01/`.
