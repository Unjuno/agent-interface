# Executed commands and environment record

The candidate source and decision gate were frozen before A03. A01 and A02 are retained construction STOPs; neither is retried.

## A01 construction STOP

`wslc.exe run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01:/src:ro' --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01\research\doom\map01_v39_v15_keyup_loss_a01_20261005\results\candidate-a01:/out' --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/research/doom/map01_v39_v15_keyup_loss_a01_20261005/candidate.py`

Exit 1 before release cases: `TypeError: DummyOwner() takes no arguments`. Exact stop is retained in `results/candidate-a01/STOP.json`.

## A02 construction STOP

Exact frozen command is in `FREEZE_A02.json`. Exit 1 after the normal case because the test finalizer accessed `closed` on the V4 wrapper; the injected-loss case did not start. Exact stop is retained in `results/candidate-a02/STOP.json`.

## A03 candidate

`wslc.exe run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01:/src:ro' --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01\research\doom\map01_v39_v15_keyup_loss_a01_20261005\results\candidate-a03:/out' --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/research/doom/map01_v39_v15_keyup_loss_a01_20261005/candidate_a03.py`

Exit 0; two cases retained in `results/candidate-a03/candidate.json`. Normal-release fake server down-set after batch: `[]`. Suppressed-release fake server down-set after batch: `[38]`.

## A03 independent auditor

`wslc.exe run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01:/src:ro' --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01\research\doom\map01_v39_v15_keyup_loss_a01_20261005\results\candidate-a03:/results:ro' --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01\research\doom\map01_v39_v15_keyup_loss_a01_20261005\results\audit-a03:/out' --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/research/doom/map01_v39_v15_keyup_loss_a01_20261005/audit_a03.py /results/candidate.json`

Exit 0; `PASS_RAW_AND_SOURCE_AUDIT`, 16/16 checks; scientific disposition remains `FAIL_BATCH_PHYSICAL_RELEASE_NOT_ESTABLISHED`.

## Resource notes

Before running, `wslc.exe container ps --format json` returned no active-container rows; the host GPU read-only snapshot was `0 %, 11 MiB, 16384 MiB`. These were CPU-only fake-X tests, with no GPU flag/device passed. WSLc emitted on each run: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” A03 raw observed `cpu.max=25000 100000`, `memory.max=536870912`, and `memory.swap.max=max`; these are recorded observations, not an independent proof of all resource enforcement. Every container used `--rm`.

## A04 production per-program cleanup attempt

Candidate (one frozen attempt; constructor STOP, no cases started):

`wslc.exe run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01:/src:ro' --volume 'C:\Users\junny\Documents\Codex\2026-10-03\new-chat-5\work\v39-v15-keyup-loss-a01\research\doom\map01_v39_v15_keyup_loss_a01_20261005\results\candidate-a04:/out' --workdir /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/research/doom/map01_v39_v15_keyup_loss_a01_20261005/candidate_a04_frozen_stop.py`

Exit 1 before paired cases: `AttributeError: 'NoneType' object has no attribute 'close'` during the production V2 constructor. Raw STOP is preserved at `results/candidate-a04/STOP.json`. The frozen stop rule prohibits repair and rerun. No A04 audit ran because candidate raw was not produced. WSLc emitted the existing swap-limit warning; see `FREEZE_A04.json` for source hashes and audit command.

The run used exact frozen source `candidate_a04_frozen_stop.py`, preserved and hashed in `FREEZE_A04.json`. The corrected `candidate_a05_unrun.py` was not executed.
