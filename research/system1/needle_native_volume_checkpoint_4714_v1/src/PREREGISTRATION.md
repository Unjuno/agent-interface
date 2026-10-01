# Docker-native volume vs host bind for resident online Needle snapshots

Issue #4714; successor to #4698. Allocation: `needle-native-volume-checkpoint-6842731-6842733-6842737-v1`.

## H

A Docker-native local volume will reduce resident one-row Needle feedback request→durable-ack p95 versus a Windows-host bind mount, to <=60 ms and <=0.5× matched bind p95 for every seed, while preserving exact LoRA+AdamW state and acknowledged snapshots. #4698's pre-freeze full-path construction suggested durable fsync/ack now dominates after removing worker respawn, but did not isolate storage path and is explicitly not formal evidence.

## T

Fresh seeds 6842731, 6842733, 6842737; no replacements. Fixed generator offsets: support features +2, held-out features +3, base model init +10, base minibatch +11, adapter init +20, support order +21. The one-row online update has no batch RNG. 8→16→4 base, rank-2 output LoRA, 400 base AdamW steps, fixed 16-row support pool, first 12 rows in the seeded order as arrivals, exactly 8 adapter AdamW updates on only the just-arrived row. The request includes current row index/features/derived label. Worker startup input excludes support rows/schedule and all target labels. Held-out input consists of 512 feature rows without labels and is used only for per-arrival prediction parity.

- `RESIDENT_BIND`: single owner, host bind mount checkpoint.
- `RESIDENT_VOLUME`: same single-owner code, same requests, same image/process environment, Docker local named-volume checkpoint.
- Both write canonical full adapter+AdamW snapshot through exclusive temp creation, file flush+fsync, atomic replace, parent-directory fsync, reread+identity validation, then ack. A single orchestration runs both arms sequentially per seed; arm order alternates by seed as recorded. One CPU, 2 GiB, 64 PIDs, network none, no pulls/install, source/root read-only. Raw result goes to a separate host bind.
- Construction uses only seed 6842703, separate from allocated formal seeds: `--smoke-one` checks one arrival; `--construction-full` checks all 12. Auditor construction disposition cannot return formal PASS. No separate no-model microbenchmark is part of this allocation.
- Formal auditor is in a separate container with raw host results and the native volume both mounted read-only; audit output is a separate host bind. It checks 72 snapshots, independent update/prediction oracle, request binding, worker input exclusions, durable byte hashes, actual final bytes on both storage paths, base/input hashes and five corruption controls. A copied final volume snapshot is retained in audit output and hash-bound to its source bytes.

## D

`PASS_NATIVE_VOLUME_LATENCY_SCOPED` iff there are zero audit errors, every request/snapshot/prediction exactly matches independent reference, all 72 acknowledged updates have valid durable snapshots, actual final bind and volume bytes match recorded states, and for each seed native-volume request/ack p95 <=60 ms and <=0.5× paired bind p95. Any integrity mismatch is typed FAIL; integrity pass with any latency miss is `HOLD_LATENCY_BUDGET`. Source/image/volume/auditor defects are `STOP`, not scientific failure. One frozen orchestration; no retries, tuning, seed replacement or post-result extension.

## C

Native volume may still share a slow host-backed virtual disk. Serialization, 512-row held-out prediction, host scheduling or fsync barriers may dominate. Same-container matched requests and stage timings localize the result; fixed arm-order alternation reduces, but does not eliminate, drift. Fsync+readback is not physical power-loss testing.

## U

Three synthetic seeds on one Windows/Docker Desktop and Linux VM, one local volume driver, tiny model. This is a storage-path/checkpoint-worker component result only—not adaptation quality, task transfer, Astra or GUI performance, multi-host persistence, production latency, or model/action authority.

## Construction isolation and chronology

Allocation-time main was `38359097c58035b04daf418551cbe331574f7535`. Current main lacked the additive evidence path; no branch/PR/issue collision was found for the allocation, seeds or branch. Branch is `research/needle-native-volume-checkpoint-4714-v1-20260927`; evidence path is `research/system1/needle_native_volume_checkpoint_4714_v1/`. Formal source freeze is not complete until the exact file hashes and Docker/image identities are published and read back byte-for-byte. Do not invoke `--formal` before that gate.
