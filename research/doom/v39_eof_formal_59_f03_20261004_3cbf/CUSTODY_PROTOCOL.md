# Prospective F03 custody and allocation gates — no run yet

H/T/D/C/U and four scientific cell gates remain PROTOCOL.md. This document
specifies delivery, not an expanded empirical claim. Pasteur's read-only
successor review of code commit 89b491adbed3df5fb5994d40e11bde7234ce61c2
found 0 Critical / 0 Important and judged code ready subject to separate live
allocation, frozen-input and custody gates. Exact-tree 22-control construction
retest is recorded in READER_HANDOFF_RESULT.md. This clears code review only;
do not launch until a final exact-frozen-input/custody review clears below.

## Frozen inputs and execution

Use a successor Git commit containing the final reviewed runner.py, audit.py,
audit_saved.py, PROTOCOL.md and this document plus readonly F02 candidate.py,
F01 probe.py and E05 source-closure.tar.gz. Archive exact paths from that commit;
retain SHA256 of archive and each input. No working-tree archive, mutable tag,
import from a peer checkout or module-preloaded process. Each invocation starts
a fresh Python interpreter inside a fresh owned Docker container. Pin image
sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Confirm owned VM research-6183-t0-20261003 UUID01M3ZD3J2GK283SQRFW9EW9DBZ
and no unrelated running allocation before launch. The source archive is reused
read-only; no E05/F01/F02 old output or consumed experiment is rerun.

Native container: f03-pipe-native-formal-3cbf-20261004; auditor container:
f03-pipe-auditor-formal-3cbf-20261004. Both names and output root must be absent.
Guest root /home/taka/f03-pipe-formal-3cbf-20261004, fresh input/native/export/audit/
receipts directories. No allocator outside this owned VM is required or granted.
Read-only input/root, network none, UID501, cap-dropALL, CPU1, memory1GiB,
memory-swap1GiB, pids128, private tmpfs. Before producer invocation retain id,
image/Engine inspect config, actual cgroup cpu.max/memory.max/memory.swap.max/
pids.max observations and in-container frozen input SHA checks. Engine config
is not empirical enforcement; host contention/global bounds remain unqualified.

Unpack archive into fresh guest input; compare host/guest archive SHA and all
input manifests before launch. The native container must mount both the exact
archive read-only at `/input.tar` and the unpacked tree read-only at `/input`,
plus the native output parent at `/output`. Create (do not start) the named
container first; retain full Engine inspect while it is still in `created`
state. Its entry shell then prints and verifies `/input.tar` SHA-256, prints
all eight frozen input SHA-256 values, observes UID/GID and actual cgroup
`cpu.max`, `memory.max`, `memory.swap.max`, and `pids.max`, and checks each
against fixed expected-value literals supplied from PRELAUNCH_FREEZE.md. The
complete exact native and auditor entry-shell scripts, their SHA256 values,
complete `docker create` invocations, inspect-before-start commands, one-use
start commands, output/export receipts and auditor command are frozen in the
`Executable launch bundle` appendix of PRELAUNCH_FREEZE.md. That appendix is an
external custody record, not a member of the producer's eight-file input
archive, avoiding a self-referential archive digest. Review the exact scripts
and commands there; do not reconstruct, edit, or improvise them at launch.
Only after all checks pass may the entry shell `exec` the producer exactly once:

```
python3 -B /input/research/doom/v39_eof_formal_59_f03_20261004_3cbf/runner.py /output/data
```

The container stdout is the pre-run hash/resource receipt followed by the
producer journal. A failed pre-run check exits before Python producer code;
that one-use container is retained and never restarted. After `docker start -a`,
retain stdout/stderr and Docker full inspect including id/state timestamps,
exit code/OOM/image/mounts. External observer owns receipts even if producer
exits before files or is uncatchably killed. Never restart or retry container.

## Export and saved-only audit

After producer exit, SHA every native data file and frozen input again. Retain
partial first STOP unchanged; never fabricate missing rows/summary. Copy native
data into distinct guest export, compare exact names/bytes/SHA to native; push
independent export to host and compare again. Five cells/summary inventory is
only applicable to complete four-cell result; STOP retains exposed subset.

If native exits0 with full data, run one distinct fresh saved-only auditor with
input readonly and exported data readonly at /saved, using the exact one-use
auditor create/inspect/start commands frozen in the same PRELAUNCH appendix.
Audit output at /audit is outside /saved, so exact five-file source inventory
stays intact:
python3 -B /input/research/doom/v39_eof_formal_59_f03_20261004_3cbf/audit_saved.py /saved /audit/AUDIT.json
Never run producer in auditor. Native nonzero: retain STOP and saved diagnostic
review without calling a PASS audit or replaying allocation. Auditor failure:
retain its first exit/stdout/stderr/output; no silent rewrite or second attempt.

Retain auditor full Engine inspect, initial/final input and data hashes, audit
SHA, original/export manifests, both receipts, source freeze and first outcomes.
Code/semantic audit is not full custody: independent reviewer must inspect these
artifacts and scope. Run applicable delivery CI on saved results only, then
PR/main when review/checks allow. No production controller change.

## Explicit remaining exclusions

SIGINT construction proves first-child interruption retention, not interruption
while reader active, repeated signals during cleanup, SIGKILL retention inside
producer, corrupt module loading branches, restart/concurrentconsumer/shape,
live GUI/input/game/model/integration/causal timing/physical safety/fullroadmap.
Module cache assumptions are avoided by fresh processes, not claimed broadly
repaired. Existing historical construction rows need explicit historical audit;
formal saved-only CLI must require strict new cleanup schema and sequential clocks.
