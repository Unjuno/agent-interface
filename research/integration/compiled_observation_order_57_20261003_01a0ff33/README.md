# Compiled capture-order repair — #57

**First A01 audit: FAIL_ORDER_GUARD_ENGINEERING_SCOPED.** The predeclared graph
success counts were incorrectly 24/14. The frozen eleven-value deck has four
type/sign-invalid values per site, so the correct counts are 21/11. FREEZE.json,
all 66 raw rows, first auditor and output are unchanged. The additive v2 is a
raw-only reconciliation, not a new run or retroactive first PASS.

The runtime repair addresses a different, reproduced ordering defect: a greater
sequence and changed evidence digest could let a capture from before execution
returned, or after observation returned, verify an effect and continue. The new
same-clock guard yields `stale_observation` with completed inputs and pending
effect retained; equal-time controls continue. It does not authenticate time or
independently certify application effects.

| Evidence | Original baseline | Repaired source |
| --- | ---: | ---: |
| Frozen ordinary engineering rows | 33 | 33 |
| Independent capture-order rule mismatches | 10 | 0 |
| Graph TASK_SUCCEEDED results | 21 | 11 |
| Type/sign-invalid captures retaining ValueError | 12 | 12 |

Raw SHA256: `06098bdb85b9e542118b73aa13b3a8ab448af84998b257b7bdbd62d5cc063fd5`.
The existing two-action fixture remains unchanged. Three capture sites test old,
boundary-adjacent, equal-return, future, negative and representation-invalid
timestamps. The baseline's ten extra graph successes are exactly the ten
ordering violations; no observed row was dropped. The independent declarative
oracle checks each legacy/repaired terminal summary and recorded execution/
observation payloads. Eight actual directed corruptions are retained in
CONTROLS.json; all are rejected. See PLAN.md for H/T/D/C/U and exclusions.

## Ordinary verification

- Test-first: five methods, ten failing subcases before repair; five methods
  pass afterward, including equal timestamps and preservation of pending effects.
- Entire core: 75/75 normal CPython 3.11.9, 75/75 optimized 3.11.9, 75/75
  normal CPython 3.12.14.
- Existing inert guarded X11 composition: 29/29 after providing private pinned
  python-xlib 0.33/six 1.17.0 imports. The first run's two missing-Xlib errors
  remain retained; no display or X11 input was opened.
- Existing working-source isolated portable archive: 1/1. Its deadline/import
  check does not itself exercise every new timestamp case.
- Committed-source build at `c3c78007a73182c109a54efe3477af6418e90316`:
  four isolated CPython 3.12.14 archive controls pass (equal boundaries, initial
  future capture, premature intermediate/final effect captures). The archived
  compiled module exactly matches the canonical candidate snapshot; no research
  module is imported. Build/check source is retained as shipping_archive_check_source.txt.
- Original raw auditor rejects all eight controls with zero evidence errors,
  but returns 1 because its frozen success-count gate is wrong. Additive raw-only
  audit_v2.py exits 0 with RECONCILED_RAW_ONLY_SUPPLEMENT and zero producer replay.

Command/UTC/exit/hash receipts accompany the outputs. Test logs that contain the
local workspace path are explicit public projections; original bytes/receipts
remain privately retained. PUBLICATION_PROJECTION.json binds both identities.
SOURCE_BYTES.json documents canonical Git LF versus actual working-source bytes.

## Revalidation and scope

`python audit_v2.py` in this directory rechecks exact source/raw/first-output
pins, declarative counts and stored mutation witnesses without executing the
runtime. `python audit.py` intentionally reproduces the preserved first FAIL.
The one-shot comparison entry refuses to overwrite raw.jsonl. Source copies are
archival; production never imports this package. Existing core/native workflow
test scopes exclude research/integration archives.

No formal/live allocation, GUI, model, GPU, container or shared runtime resource
was used. No live effect, physical release, clock authenticity, matched token/
latency improvement, broad reliability or completion of #57/#59 is claimed.
The proposed source change requires nonauthor content and current-tree approval
before main application. Existing #6863 sequence-type and #6900 evidence-reference
repairs remain separate delivery lanes.
