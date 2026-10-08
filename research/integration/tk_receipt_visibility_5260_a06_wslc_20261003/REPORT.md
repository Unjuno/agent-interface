# #5260 A06 — phase ambiguity boundary construction

METHOD_PASS_CONSTRUCTION_ONLY/errors[] and H_PASS_BOUNDARY_CONSTRUCTION_ONLY.
One new8-writer construction, no GUI, keyboard, click, Save or focus action.

| Controlled delayed phase | Cells | Old-stamp50ms age exceeded |
| --- | --- | --- |
| PUBLISH_DELAY100ms |4|4|
| READER_DELAY100ms |4|4|

Each phase crosses HOST_BIND/CONTAINER_TMP and idle/cpu_busy once, seed52606026.
All8 first reads bind exact immutable token bytes, source/PID/fixture and
writer write/flush/fsync/replace plus every reader attempt interval. All8
writers and four busy children exited0. Candidate once15:35:46.144856–
15:35:51.102757UTC exit0/4.9577s; separate auditor once15:36:18.820699–
15:36:19.335133UTC exit0/0.5147s. These invocation times are not benchmarks.

In the same HOST_BIND/idle controls, row000 had an imposed reader delay:
receipt publication ended40.550287ms after oldstamp, first read ended
109.324815ms after oldstamp. Row001 imposed publication delay instead:
publication ended113.230400ms after stamp, first read ended121.880910ms.
Both final age labels would be expired, but the full trace distinguishes
the induced phase. One cell each, artificial delays; no distribution,
filesystem speed ranking or natural-host-load inference.

This supports retaining publication **intervals** and first read/parse/seen
clocks separately from an app event or pre-write timestamp. It does not
identify A05row009's historical cause, prove focus freshness/current target,
or justify resetting an old event's age at publication. A target could
change while a receipt is being published/read; a fresh publication does
not make admission atomic with the app.

Source frozen at7c22db138e7a82dfd86522e132e34f1f14bdd9bc, FREEZE readback
viaGitHubMCP MATCH before invocation. All8 frozen source/plan/test hashes
remain unchanged.12 tests before input-free construction;2 new retained
tests RED(missing verifier) then GREEN; review adds one busy-overlap test,
15 current tests pass.15 temporary
raw corruptions rejected by readonly validation; original source/raw/streams
unchanged. Stronger post-outcome route checker also binds HOST receipt.json
to retained read bytes and checks private/tmp unique path syntax.

Actual container-local/tmp files disappear with disposable container;
their exact first-read bytes and writer/reader trace remain. HOST_BIND
original receipt.json and read bytes both remain. These are source/path/
file custody, not privileged focus/sensor/authority evidence. Independent
auditor imports neither candidate nor writer implementation. Author self-
review is distinct from raw audit and required GitHub code review/CI.

PR review found the frozen auditor did not require busy-child overlap.
Its consumed source/audit remain unchanged. A new readonly typed overlap
gate is RED->GREEN and rejects before/after/boundary-only/invalid clocks.
The four actual busy windows overlap writer-stamp-to-first-read by
102879487/121809879/100565360/114178585ns, respectively rows2/4/5/7; they
contain those entire four measured phases. Extra raw-copy before-phase
worker control is rejected. This is interval custody, not cap enforcement
or quantified CPU load. All8 frozen source hashes remain unchanged.

Same cachedWSLc image217851fe68e7/linuxamd64/Python3.13.5; networknone/
sourceRO/candidateinputRO/uid65534/requestCPU0.5/512M. Both WSL swap-limit
warnings retained; effective memory caps, OOM prevention or migration benefit
unproven. No shared service/globalconfig/other-owner allocation, userdisplay,
GPU/model/external effect or product/defaultage/defaultwait changed.

Prospective#5260#5970636206/#5085#5970636345; release#5085#5970649842.
RawSHA256 f36a8273802ee47c8bd5a093f7fb86b86d75169bb5fe96c592bde0c8681654f6;
auditstdout affc5128b83751dfd139274cae3d108b32af894c44a805a1e05f785470cdfceb.
Keep#5260/#5296 and broader roadmap open. Next: a fresh live focus successor
with full publication/read/admission samples, not replay or age relaxation.
