# Issue #5134 — successor allocation -03 after terminal -02 STOP

This is successor allocation `needle-publication-orbstack-bind-5066-20260928-03`,
not a retry or relabel of -01 or terminal -02. Preserve #5073, PR #5109, PR
#5152, their source/raw/audit outputs, and predecessors #5045/#5066 byte-for-byte.
Allocation -02 ended before Docker with a marker-freshness STOP and a concurrent
inventory STOP; it produced no scientific observations. Independent audit
#5861943985 identified the two correctness defects fixed here.

## H / T / D / C / U

**H.** On a macOS-host OrbStack bind mount, seven monotonic package transitions
publish atomically: each of four readers per phase retains the previous
descriptor and, after replacement returns, reads the exact next generation by
fresh path. Invalid-digest and stale-base proposals yield without changing
ACTIVE; matched in-place writes expose partial bytes.

**T.** One pinned linux/arm64 OrbStack formal allocation, using the exact seed
blob and generations 3789–3795. One runner invocation followed only on exit 0
by a separate auditor. The raw/receipt pair is copied to `/in` with a SHA-256
manifest, mounted read-only; auditor output is a separate writable `/out`.
The sole formal output path is frozen as
`/tmp/unjuno-5134-orbstack-publication-20260928-03`; a different CLI path is
rejected before Docker access. Current-main and named exclusive queue/owner
markers are mandatory. No retries.

**D.** PASS requires 56 concurrent + 28 post rows and 28 unsafe rows to
reconcile, all descriptor timestamps ordered `open < replace-start <
replace-return < read-start < read-end`, exact old/new bytes, rejected
invalid/stale proposals, partial unsafe prefixes, and all ten corruption
controls rejected. A contrary valid observation is scoped FAIL;
provenance/resource/audit defect is STOP.

**C.** Same seed-derived package, schedule, readers, image, path and resource
limits in both arms; only validated `os.replace` versus diagnostic in-place
rewrite differs.

**U.** One host, OrbStack context/version, Linux/arm64 image, path and synthetic
fixed schedule. No cross-platform equivalence, crash durability, production,
GUI/model/task quality, authority, or latency claim.

## Corrected independent-audit boundary

The independent auditor imports neither `runner.py` nor `protocol.py`. It
validates the `/in` manifest against both input bytes, requires `/in` and `/src`
read-only and separate `/out` writable, and reconstructs distinct formal and
auditor Docker commands from the receipt. It explicitly checks both descriptor
read-start and read-end timestamps after replacement returns. Construction
tests exercise valid/mutated manifest, mount, command, and timestamp cases.

## Formal boundary and disposition

Host construction tests do not launch Docker and are not a scientific result.
A formal launch requires exact current-main/source/output identity, fresh owner
and queue markers naming this allocation/main, the pinned image/platform,
OrbStack context, and a conflict-free inventory. The formal and audit mounts
have isolated writable outputs, bounded resources, dropped capabilities,
network none and no-new-privileges. Any formal invocation/output consumes this
allocation; preserve every STOP and do not retry.

The -02 allocation and its lease are terminal. Do not infer a new lease from
any release, idle daemon, or clean inventory. The observed
`cans-hg-n128-dt0.001` container remains untouched and its owner is unconfirmed.
Reconcile active requests on #5085 and await an exact named assignment before
formal container launch. A STOP is not a scientific conclusion.
