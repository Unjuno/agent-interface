# Issue #5905 image-only T0.2 A02

Status before formal execution: preregistered; candidate=0, independent auditor=0, retries=0. Do not read this as a result until RUN.json is populated.

A01 remains at looming_yield_5905_t0_20261001_01 with its original main-drift STOP. This successor gives the candidate raster bytes, source timestamps, and track IDs only; latent contact/control labels are held in the auditor-only input. It measures a narrowly authored set of approach and confound sequences, including a nonapproach animation whose full pixel/timing/track sequence is identical to approach-1.

The experiment compares a finite grid of endpoint pixel-change, target-area growth, and secant-TTC thresholds at equal five-frame budget and at most one false YIELD among seven controls. The chosen TTC threshold and simulated release latency are fixed in PREREG.md. This is a synthetic method experiment, not a live game, controller, safety, damage, or product result.

inputs/observations.json.gz and inputs/truth.json.gz are exact gzip copies of the inputs used in the containers. Inflate them to reproduce the commands in RUN.json. The candidate input omits truth labels. The raw result retains decoded-frame hashes, per-frame target measurements, cue decisions and full threshold grids.

Container: WSLc 3.0.1.0; cached python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016; image config ID sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364; linux/amd64; network none; one CPU and 512 MiB requested; GPU none. Requested CPU/memory limits are not treated as independently measured enforcement.