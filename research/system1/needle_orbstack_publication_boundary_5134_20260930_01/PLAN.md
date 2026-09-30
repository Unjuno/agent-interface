# Issue #5134 — OrbStack publication boundary pilot 2026-09-30-01

This is a separate, construction-class boundary experiment. It does not invoke,
create output for, or consume formal allocation
`needle-publication-orbstack-bind-5066-20260928-03`. Its purpose is to obtain
fresh, real OrbStack bind-mount observations on one transition while the seven-
phase formal allocation is awaiting its owner and queue markers.

## H / T / D / C / U

**H.** On this macOS host's OrbStack bind mount, one validated same-directory
`os.replace` exposes the complete new package by fresh path lookup while four
independent readers retaining pre-replace descriptors still read the complete
old package. A matched in-place truncate/write control exposes the strict
first-half prefix while the writer is paused.

**T.** One Docker invocation on the frozen OrbStack context and pinned
`linux/arm64` image; network disabled, read-only container root, read-only
source mount, one dedicated writable output mount, 0.25 CPU, 512 MiB, 32 PIDs,
all capabilities dropped, no-new-privileges. Four spawned reader processes,
one atomic transition based on immutable seed generation 3788, and one
barrier-controlled in-place control. `OBSTAC_CONSTRUCTION=1`. A separate
network-none auditor container consumes raw and receipt from a read-only
`/in` mount and writes only to `/out`. Unique pilot allocation and output path;
no retry. Raw contains exact observed bytes as base64. The source commit and
file hashes are frozen before container execution.

**D.** `PASS_BOUNDARY_PILOT_SCOPED` requires four unique child PIDs and zero
exits, each old descriptor to return byte-exact valid generation 3788 after
replacement returns, each fresh-path read to return byte-exact valid
generation 3789, the replacement timestamps to be ordered, and all four
in-place readers to capture exactly the strict first-half prefix before writer
completion. Independent audit must reconstruct all bytes, digests, generations,
timings, identities, image, context, mounts, source and freeze. Any contrary
complete observation is `FAIL_BOUNDARY_PILOT`; any missing/invalid provenance,
denominator, image, context, mount or audit evidence is `STOP_BOUNDARY_PILOT`.

**C.** Both arms use the same exact seed-derived old/new JSON package bytes,
reader count and OrbStack bind root. Only atomic same-directory replacement
versus diagnostic truncate/write differs. This pilot measures one transition,
not the seven-phase schedule.

**U.** One host, OrbStack version/context, pinned image/platform, bind path,
synthetic seed and one transition. It does not meet the formal 56 concurrent +
28 post + 28 unsafe denominators; does not release or replace allocation -03;
does not establish cross-platform behavior, crash durability, production
safety, GUI/model/task quality, authority, or latency.

## Frozen execution

See `FREEZE.json` for source and input identities, exact container image and
limits, allocation, and dedicated output path. `run.py` is the sole container
entrypoint; `audit.py` is the independent audit entrypoint and imports no
runner/protocol code. Preserve every result, including STOP/FAIL; never retry
this pilot allocation.
