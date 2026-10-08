# Issue #6669 — WSLc control-plane under bounded pressure

Allocation WSLC-CONTROL-PLANE-6669-T1-20261003-A01; frozen from main `e7f11cdc2cdee42b0f745add6c4a93fc641abe6d`. Current main advanced during the experiment; the PR branch preserves that exact freeze and updates the index against current main.

## H — Hypothesis

A distinct WSLc session with a 1 GiB VM ceiling and one CPU can retain its management/control plane while a single network-isolated container creates bounded memory pressure, and can stop and remove that container cleanly.

## T — Test

WSLc 3.0.1.0, kernel 6.18.40.1-1, Microsoft.WSL.Containers SDK 3.0.1. The separately created session was named `codex-wslc-audit-6669-20261003`, CPU=1, memory=1024 MiB. Candidate used pinned image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--network none --pull never --memory 768M --cpus 1`. The pressure candidate touched 640 MiB in 8 MiB steps and held up to 60 seconds. A matched no-pressure control touched 32 MiB. Both installed a SIGTERM handler and emitted a raw receipt before clean exit. See FREEZE.md and amendments for the preregistration history.

## D — Data

The pressure-ready sample reported guest MemTotal=922048 kB and MemAvailable=99564 kB; at SIGTERM, MemAvailable=98076 kB. The minimum observed was below the frozen 128 MiB pressure threshold. Container stats sampled 652.3 MiB / 768 MiB. cgroup memory.max was 805306368 bytes, all memory.events counters were zero, memory.swap.max was max, and WSLc warned that swap-limit capabilities were unavailable.

During the pressure hold, all 11 control operations exited 0 within 15 seconds. The first operation started 14.328 seconds after pressure-ready. stop --time 10 completed in 161 ms; the candidate logged SIGTERM (15), exited 0, and was removed. The final container list was empty. The matched 32 MiB no-pressure control logged SIGTERM, exited 0, and stopped in 124 ms.

The standalone WSLc auditor passed. Its three independent corruption checks rejected false-success, missing stop acknowledgement, and missing cleanup. Raw outputs, complete operation records, and SHA-256 checksums are retained in this directory.

## C — Controls and causal interpretation

**Method-scoped PASS:** these observations support control-plane availability and clean stop/remove for this one bounded synthetic pressure case on WSLc 3.0.1.0.

Earlier candidates lacked a SIGTERM handler while running as PID 1. They took about 10.17 seconds and exited 137 in both the pressure and no-pressure arms. The matched SIGTERM-aware arms stopped in 124–161 ms. Linux PID namespace documentation limits signals from an ancestor namespace to PID 1 to signals for which that init process has established a handler: https://man7.org/linux/man-pages/man7/pid_namespaces.7.html. The 137 result was therefore a candidate-process confound and is not evidence of a WSLc pressure-specific defect.

## U — Uncertainty and limits

This test does not demonstrate hard per-container memory enforcement: allocation remained below the 768 MiB memory.max, memory.events remained zero, and swap was unlimited. The isolated session VM ceiling was the resource bound. No OOM, host-wide pressure, Docker comparison, GPU, GUI, model, or representative application workload was tested. Do not generalize to other WSLc versions, configurations, or workloads.

## Reproduction and audit

See `commands-final.txt`, `candidate-sigterm.py`, `audit-final-v3.py`, `audit-mutations-v3.py`, `AUDIT-RUN-v3.txt`, and `SHA256SUMS.md`. Issue #6669 contains the preregistration amendments and the result readback.
