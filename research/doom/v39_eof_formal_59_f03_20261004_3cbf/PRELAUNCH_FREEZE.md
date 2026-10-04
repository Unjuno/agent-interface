# F03 exact input freeze and non-scientific custody preflight

Status: **PRELAUNCH REVIEW REQUIRED — no formal candidate or auditor has run.**

## Research question and decision rule

- H: F02 persistent typed EOF/JSON notifications preserve the ready/terminal FIFO and the second wait failures relative to the exact E02 live-child EOF control.
- T: Four fresh sequential child processes, in fixed order `baseline_eof`, `candidate_eof`, `candidate_events_eof`, `candidate_json`; one pass, no retries.
- D: Retain each raw row, exact outcomes/causes, positive sequential monotonic clocks, source pins, process identity, event handshake and post-cleanup liveness. The producer summary remains provisional until external native exit 0; only then may a distinct saved-only auditor inspect exported saved bytes.
- C: Eight frozen source inputs listed below; E02 archive, F02 candidate and F01 helper hashes are checked by the producer. Pinned Linux/arm64 image `sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b`. Dedicated VM `research-6183-t0-20261003`, UUID `01M3ZD3J2GK283SQRFW9EW9DBZ`; network none, read-only image/input, UID/GID 501, CPU 1, memory 1 GiB, memory-swap 1 GiB, pids 128, private 256 MiB `/tmp`.
- U: This says nothing about GUI/input, model use, DOOM/gameplay, end-to-end controller integration, restarts, concurrent consumers, normal-exit traces, causal latency, safety, or production adoption. A result is bounded to this four-cell pipe-notification control.

Expected cells and exact first-unexpected-cell STOP rule are in `PROTOCOL.md`. Formal containers, output root, source archive, native output, export, and audit are single-use; no retries or relabeling. The native failure retained at `methods/READER-SIGNAL-v2.log` is construction evidence and is not a scientific observation.

## Immutable inputs

The frozen input tree is commit `6d8387caa8a004ebbdadc377e499b85b3b3a10db` / tree `338afba37b8c9fe28fe410ec56a5c0788c96e614`. Exact eight-file archive SHA-256: `786dafda0057e809b5b5f32488899a544e07ad856323d0f635017681704b6344`; host and guest copies match. The archive contains only:

```
623fc63fb7d7f0ea87bd39109eb0a1bdcb5da7d5615cca2f85fcf2921821d386  research/doom/v39_eof_formal_59_f03_20261004_3cbf/runner.py
fd6d766f162ce7bc4e42890bb720245fc906ea11985303b0b9b97dd30203d5d2  research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit.py
ebfcef6197e7f121c9eb7d1c6822ac5d6fc3c1c9c3a4b2530517ad8a6de6d1d6  research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit_saved.py
4438143d2ae3b8ea5448ffb9f6fd4ebe6c57785dc53951f6e2f35c0d32784d68  research/doom/v39_eof_formal_59_f03_20261004_3cbf/PROTOCOL.md
4b125b90f8cafc922c230ee9c56164b1f45cfa2459b91df65709a7a6b2a842f3  research/doom/v39_eof_formal_59_f03_20261004_3cbf/CUSTODY_PROTOCOL.md
2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1  research/doom/v39_eof_59_f02_20261004_3cbf/candidate.py
8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0  research/doom/v39_os_pipe_59_f01_20261004_3cbf/probe.py
d1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db  research/doom/v39_native_fault_59_e05_20261004_3cbf/source-closure.tar.gz
```

No old F01/F02/E05 output is included or rerun. The archive is transferred unchanged; no mutable checkout or peer branch is mounted.

## Setup-only container observation

The earlier `f03-final-preflight-40b57f74f4` and `f03-final-preflight-bd0177147a` are preserved as superseded setup evidence. The exact frozen-input setup container `f03-final-preflight-6d8387caa8` printed and checked `/input.tar` SHA-256 `786dafda0057e809b5b5f32488899a544e07ad856323d0f635017681704b6344`, all eight file hashes above, `uid=501 gid=501 groups=501`, and cgroup `cpu.max=100000 100000`, `memory.max=1073741824`, `memory.swap.max=0`, `pids.max=128`. Its inspect records network `none`, CPU 1, 1 GiB memory and memory-swap, read-only root and archive bind, all capabilities dropped, no-new-privileges, UID/GID 501, and private tmpfs. ExitCode=0, OOMKilled=false, `2026-10-04T01:00:33.001834798Z`–`2026-10-04T01:00:33.086242046Z`. Full stdout and full Engine inspect are preserved in `methods/FINAL-PREFLIGHT-v3.log` and `methods/FINAL-PREFLIGHT-v3-inspect.json`; host/guest transfer receipt is `methods/FINAL-ARCHIVE-HASH-v3.log`. These are actual setup-container observations only; host contention/global bounds are not inferred.

The native container must mount both the exact archive at `/input.tar` and the unpacked input tree at `/input`, each read-only. It will be created and inspected before start. The entry shell prints and checks the archive hash, all eight input hashes, UID, and actual cgroup values against fixed literals supplied from this freeze, then `exec`s the runner only if every check passes. A mismatch exits before candidate code runs; the one-use container is never restarted. The final immediate prelaunch check must again compare host and guest archive hashes.

Issue #59 notices `5975102690` and `5975194860` record the planned sequence and the previous input revision; publish a final notice for the archive hash above before launch. Independent review of the final invocation path is pending. Immediately before formal launch, recheck VM UUID/state, all running containers, the two formal container names, and output root; retain fresh evidence. Until the final notice, independent review, and immediate checks clear, do not launch either formal container.
