# Worker Quickstart

Updated 2026-10-15. Read this page, [CURRENT_GOAL.md](CURRENT_GOAL.md), and the
selected row in [WORKER_WORK_MAP.md](WORKER_WORK_MAP.md). Expand history only
when the chosen question requires it.

## Start one bounded piece of work

1. Identify the concrete unmet capability and strongest simple baseline. Read the
   selected Issue and relevant open/closed PRs, current source and evidence.
2. Check overlap for the exact files, experiment and resources you will use.
   Record a branch, additive output path and narrow scope in the existing owning
   Issue/coordination mechanism. An Issue comment is coordination, not an atomic lock.
3. For shared GUI/GPU/runtime or a formal run, verify current ownership and an
   unused allocation through the applicable mechanism. Otherwise begin independent
   offline analysis, code or tests; do not wait for unrelated shared resources.
4. Execute a finite experiment/repair. Separate construction from formal allocation,
   preserve first outcomes and state what result changes the adoption decision.
   Keep STOP/HOLD/FAIL scoped to its allocation; it does not stop unrelated work.
5. Run relevant local checks. Deliver reviewable changes and evidence through a PR;
   integrate when actual permissions/protection and required checks permit it.
6. Update the owning Issue with evidence, limits and next action; release only your
   own resources. Do not require another worker or invented reviewer quota to do
   ordinary authorized work.

## Where to put things

| Material | Destination |
|---|---|
| Current priority / work to choose | Current goal / work map; links, not repeated histories |
| Idea | [Idea ledger](ideas/README.md): hypothesis, existing evidence, dependencies, next test and decision |
| Result / failed attempt | [Research placement guide](../research/README.md#research-routing); raw and scope preserved |
| Runtime change | Actual supported caller/backend, meaningful regression and relevant local checks |
| Cleanup | [Consolidation plan](REPOSITORY_CONSOLIDATION.md); verify custody before deleting anything |

Eligible new isolated CPU/container studies can use Windows WSLc; qualify actual
host support and enforcement, freeze image/source/argv, and keep network/pull
disabled where specified. macOS or a protocol requiring Engine/Compose uses its
supported runtime. Runtime choice does not renew a consumed allocation.

Historical reservations and closure corrections are in the selected Issue/PR and
[the previous quickstart](WORKER_QUICKSTART_HISTORY_20261015.md). In particular,
[#5085](https://github.com/Unjuno/agent-interface/issues/5085) was closed when
checked 2026-10-15; do not treat that old GPU log as a universal current queue.
Revalidate the resource you actually need. Closure alone proves no resource release.
