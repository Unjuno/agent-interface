# F03 exact input freeze and non-scientific custody preflight

Status: **FINAL INVOCATION REVIEW REQUIRED — no formal candidate or auditor has run.** This document freezes exact one-use invocations; it does not authorize execution. Launch still requires independent review of this revision and a fresh immediate prelaunch inventory.

## Research question and decision rule

- H: F02 persistent typed EOF/JSON notifications preserve the ready/terminal FIFO and the second wait failures relative to the exact E02 live-child EOF control.
- T: Four fresh sequential child processes, in fixed order `baseline_eof`, `candidate_eof`, `candidate_events_eof`, `candidate_json`; one pass, no retries.
- D: Retain each raw row, exact outcomes/causes, positive sequential monotonic clocks, source pins, process identity, event handshake and post-cleanup liveness. Producer summary remains provisional until external native exit 0; only then may a distinct saved-only auditor inspect exported saved bytes.
- C: Eight frozen source inputs below; E02 archive, F02 candidate and F01 helper hashes are checked by the producer. Pinned Linux/arm64 image `sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b`. Dedicated VM `research-6183-t0-20261003`, UUID `01M3ZD3J2GK283SQRFW9EW9DBZ`; network none, read-only root/input, UID/GID 501, CPU 1, memory 1 GiB, memory-swap 1 GiB, pids 128, private 256 MiB `/tmp`.
- U: No claim about GUI/input, model use, DOOM/gameplay, end-to-end controller integration, restarts, concurrent consumers, normal-exit traces, causal latency, safety, or production adoption. Result is bounded to this four-cell pipe-notification control.

Expected cells and exact first-unexpected-cell STOP rule are in `PROTOCOL.md`. Formal container names, output root, source archive, native output, export and audit are single-use; no retries or relabeling. The native failure retained at `methods/READER-SIGNAL-v2.log` is construction evidence, not a scientific observation.

## Immutable eight-file input

Frozen source commit `0f8700502ef5778fb2b3f5a37123d5b983422c5a`, tree `eeba8542507ba9406a869f6ba93c532f4c6f86ae`. Reproduce the exact archive from that public commit with the following command; two independent invocations on this host were byte-identical. Exact archive SHA-256 `8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5`. Host and guest copies match. Eight member hashes:

```
git archive --format=tar 0f8700502ef5778fb2b3f5a37123d5b983422c5a -- research/doom/v39_eof_formal_59_f03_20261004_3cbf/runner.py research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit.py research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit_saved.py research/doom/v39_eof_formal_59_f03_20261004_3cbf/PROTOCOL.md research/doom/v39_eof_formal_59_f03_20261004_3cbf/CUSTODY_PROTOCOL.md research/doom/v39_eof_59_f02_20261004_3cbf/candidate.py research/doom/v39_os_pipe_59_f01_20261004_3cbf/probe.py research/doom/v39_native_fault_59_e05_20261004_3cbf/source-closure.tar.gz > input.tar
```

```
623fc63fb7d7f0ea87bd39109eb0a1bdcb5da7d5615cca2f85fcf2921821d386  research/doom/v39_eof_formal_59_f03_20261004_3cbf/runner.py
fd6d766f162ce7bc4e42890bb720245fc906ea11985303b0b9b97dd30203d5d2  research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit.py
ebfcef6197e7f121c9eb7d1c6822ac5d6fc3c1c9c3a4b2530517ad8a6de6d1d6  research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit_saved.py
4438143d2ae3b8ea5448ffb9f6fd4ebe6c57785dc53951f6e2f35c0d32784d68  research/doom/v39_eof_formal_59_f03_20261004_3cbf/PROTOCOL.md
9d84620ecffd4ba28eaa586bd44f19c2ebfc92d81062734c4a6aca4e57af871a  research/doom/v39_eof_formal_59_f03_20261004_3cbf/CUSTODY_PROTOCOL.md
2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1  research/doom/v39_eof_59_f02_20261004_3cbf/candidate.py
8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0  research/doom/v39_os_pipe_59_f01_20261004_3cbf/probe.py
d1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db  research/doom/v39_native_fault_59_e05_20261004_3cbf/source-closure.tar.gz
```

The separately retained manifest is `methods/input.SHA256` (SHA-256 `86882b20a319bfacb788fddbd81630dd6f4b1da93e4062eb0bf455d016f60c3d`). The archive is transferred unchanged; no working-tree archive, mutable tag, peer checkout, or module-preloaded process is used. The native and auditor entry scripts are exact host-side custody artifacts mounted read-only, not members of the eight-file research input: native SHA-256 `c6d401e77c72dc5c2d636ecb6ca5b5252045dbd406eaf1fa2418790b7c092882`, auditor SHA-256 `357ad84d5298f9399307c1a854efad4a1ccb37b189d4c217f291def40f52a002`.

## Setup-only container evidence

The exact v6 input is copied to `/home/taka/f03-custody-bundle-v6/input.tar`, unpacked to `/home/taka/f03-formal-input-v6`, and independently matched against the manifest. Host and guest archive SHA-256 both equal `8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5`; all eight extracted input files verify. Re-running the exact `git archive` command from the public frozen commit produced byte-identical output.

Setup-only container `f03-final-preflight-v6-0f8700502e`, pinned image above, was created then inspected while `created` before its only start. It mounted the exact archive, unpacked tree, manifest and both entry scripts read-only; network none, CPU 1, memory and memory-swap 1 GiB, read-only root, all capabilities dropped, no-new-privileges, UID/GID 501 and private tmpfs. Its stdout checked archive digest, all eight input hashes, UID/GID, actual cgroup `cpu.max=100000 100000`, `memory.max=1073741824`, `memory.swap.max=0`, `pids.max=128`, and printed `PREFLIGHT_V6_PASS`. Exit 0, OOM false, started `2026-10-04T01:20:44.472126935Z`, finished `2026-10-04T01:20:44.565693509Z`. Full stdout and Engine inspect are retained in `methods/FINAL-PREFLIGHT-v6.log` and `methods/FINAL-PREFLIGHT-v6-inspect.json`; archive receipt is `methods/FINAL-ARCHIVE-HASH-v6.log`. After final entry-script update, the guest copies of both scripts, manifest and archive were rehashed against the exact constants in this freeze; receipt is `methods/FINAL-ENTRY-HASH-v6.log`. This is setup-only evidence; it does not establish host contention or global resource bounds.

Predecessor container `f03-final-preflight-v4b-796e5440be` validated the prior digest and is superseded. Its predecessor `f03-final-preflight-v4-796e5440be` had a missing manifest mount, remains `created`, and was never started. No candidate code ran in either predecessor.

Earlier setup-only records for v1–v4 are superseded. The v4 create-only container with a missing manifest mount remains unstarted and retained; no candidate code ran. Only the exact v6 preflight above applies to this freeze. No formal container has been created.

## Executable launch bundle — exact commands

Fixed guest paths:

```
VM: research-6183-t0-20261003 (UUID 01M3ZD3J2GK283SQRFW9EW9DBZ)
IMAGE: sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b
INPUT: /home/taka/f03-formal-input-v6
BUNDLE: /home/taka/f03-custody-bundle-v6
ROOT: /home/taka/f03-pipe-formal-3cbf-20261004
NATIVE: f03-pipe-native-formal-3cbf-20261004
AUDITOR: f03-pipe-auditor-formal-3cbf-20261004
```

Exact guest custody bundle file SHA-256 values (verify these at the immediate gate):

```
native-entry.sh: c6d401e77c72dc5c2d636ecb6ca5b5252045dbd406eaf1fa2418790b7c092882
auditor-entry.sh: 357ad84d5298f9399307c1a854efad4a1ccb37b189d4c217f291def40f52a002
input.SHA256: 86882b20a319bfacb788fddbd81630dd6f4b1da93e4062eb0bf455d016f60c3d
input.tar: 8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5
```

Before launch, recheck the VM UUID/state with `orbctl info research-6183-t0-20261003`. On that VM as `taka`, run `sudo -n docker ps --no-trunc`; it must show no unrelated running container. Check both formal names absent with `sudo -n docker inspect NAME` (a present name is STOP; do not remove it), and require `test ! -e /home/taka/f03-pipe-formal-3cbf-20261004`. Recompute `shasum -a 256 /tmp/f03-formal-frozen-v6.tar` on host and `sha256sum /home/taka/f03-custody-bundle-v6/input.tar` on guest; both must equal the archive digest above. Recompute and compare the guest `native-entry.sh`, `auditor-entry.sh`, and `input.SHA256` hashes to the values above. Record all output immediately before creating a formal container. Any mismatch or unrelated running Docker container is STOP; do not launch.

After those checks pass, create the four empty output subdirectories once:

```
mkdir -p /home/taka/f03-pipe-formal-3cbf-20261004/native /home/taka/f03-pipe-formal-3cbf-20261004/export /home/taka/f03-pipe-formal-3cbf-20261004/audit /home/taka/f03-pipe-formal-3cbf-20261004/receipts
```

Exact native create command (run on the owned VM as `taka`; this does not start it):

```
sudo -n docker create --name f03-pipe-native-formal-3cbf-20261004 --platform linux/arm64 --network none --cpus 1 --memory 1g --memory-swap 1g --pids-limit 128 --read-only --cap-drop ALL --security-opt no-new-privileges --user 501:501 --tmpfs /tmp:rw,nosuid,size=256m --workdir /input --mount type=bind,src=/home/taka/f03-formal-input-v6,dst=/input,readonly --mount type=bind,src=/home/taka/f03-custody-bundle-v6/input.tar,dst=/input.tar,readonly --mount type=bind,src=/home/taka/f03-custody-bundle-v6/input.SHA256,dst=/custody/input.SHA256,readonly --mount type=bind,src=/home/taka/f03-custody-bundle-v6/native-entry.sh,dst=/entry.sh,readonly --mount type=bind,src=/home/taka/f03-pipe-formal-3cbf-20261004/native,dst=/output sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b /bin/sh /entry.sh
```

Before any start, save full `sudo -n docker inspect f03-pipe-native-formal-3cbf-20261004` to `ROOT/receipts/native-created-inspect.json`; independently verify state `created`, pinned image, exact mounts, read-only input/archive/script, writable native output only, network none, and all resource/security fields match this freeze. If not exact, STOP and do not start. Exact one-use start and external exit receipt:

```
set +e
sudo -n docker start -a f03-pipe-native-formal-3cbf-20261004 > /home/taka/f03-pipe-formal-3cbf-20261004/receipts/native-stdout.log 2>&1
rc=$?
printf '%s\n' "$rc" > /home/taka/f03-pipe-formal-3cbf-20261004/receipts/native_exit.txt
sudo -n docker inspect f03-pipe-native-formal-3cbf-20261004 > /home/taka/f03-pipe-formal-3cbf-20261004/receipts/native-final-inspect.json
exit "$rc"
```

Never restart or retry. Retain even a pre-exec failure. Only if native external exit is 0 and the four-cell output is complete, copy native data once to the initially empty export directory (`cp -a ROOT/native/data/. ROOT/export/`), compare exact relative filenames, bytes and SHA-256 native↔export, and save both inventories/receipts. Push the independent export to host and compare again. Nonzero or incomplete native output is a retained STOP and forbids auditor start.

Only after the above success gate, require the retained external `ROOT/receipts/native_exit.txt` to contain exactly `0\n`. Create the auditor container once with the exact settings/mounts below (it is not created before candidate success):

```
sudo -n docker create --name f03-pipe-auditor-formal-3cbf-20261004 --platform linux/arm64 --network none --cpus 1 --memory 1g --memory-swap 1g --pids-limit 128 --read-only --cap-drop ALL --security-opt no-new-privileges --user 501:501 --tmpfs /tmp:rw,nosuid,size=256m --workdir /input --mount type=bind,src=/home/taka/f03-formal-input-v6,dst=/input,readonly --mount type=bind,src=/home/taka/f03-custody-bundle-v6/input.tar,dst=/input.tar,readonly --mount type=bind,src=/home/taka/f03-custody-bundle-v6/input.SHA256,dst=/custody/input.SHA256,readonly --mount type=bind,src=/home/taka/f03-custody-bundle-v6/auditor-entry.sh,dst=/entry.sh,readonly --mount type=bind,src=/home/taka/f03-pipe-formal-3cbf-20261004/export,dst=/saved,readonly --mount type=bind,src=/home/taka/f03-pipe-formal-3cbf-20261004/audit,dst=/audit --mount type=bind,src=/home/taka/f03-pipe-formal-3cbf-20261004/receipts/native_exit.txt,dst=/receipt/native_exit.txt,readonly sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b /bin/sh /entry.sh
```

Save/inspect the auditor in `created` state with the same exact checks before its sole start:

```
set +e
sudo -n docker start -a f03-pipe-auditor-formal-3cbf-20261004 > /home/taka/f03-pipe-formal-3cbf-20261004/receipts/auditor-stdout.log 2>&1
rc=$?
sudo -n docker inspect f03-pipe-auditor-formal-3cbf-20261004 > /home/taka/f03-pipe-formal-3cbf-20261004/receipts/auditor-final-inspect.json
exit "$rc"
```

The auditor entry script checks archive/member hashes, UID/GID, actual cgroups and native exit receipt before executing exactly once: `python3 -B /input/research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit_saved.py /saved /audit/AUDIT.json`. No producer is run in the auditor. Retain its full inspect, initial/final input and data hashes, audit SHA, original/export manifests and first outcomes. Any audit failure is retained unchanged; no second attempt.

## Remaining limits

Independent review must inspect this exact launch bundle and confirm the final Issue #59 notice for archive digest `8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5`. Immediately before formal container creation repeat all VM, running-container, container-name, output-root, host/guest archive and script/manifest hash checks above and preserve the output. Until the v6 setup preflight, final review, notice and immediate checks pass, do not create or start either formal container.

SIGINT construction proves first-child interruption retention, not interruption while reader active, repeated signals during cleanup, SIGKILL retention inside producer, corrupt module loading branches, restart/concurrentconsumer/shape, live GUI/input/game/model/integration/causal timing/physical safety/fullroadmap. Host contention and global resource bounds are unqualified. This bounded pipe experiment does not close Issue #59 or the full roadmap.
