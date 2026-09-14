# Fresh transfer of a model-authored displacement condition

## Question

The fixed-context authorship probe shows that Luna and Astra can select a useful
patch on one retained frame. This study transfers the unchanged first Luna
output into fresh X11 processes and tests whether it gates an already admitted
Save step. Pointer paths remain scripted so the experiment isolates the authored
postcondition.

## Retained failures

The first preregistered allocation fails before input because the plan stores a
Windows absolute author-artifact path that WSL cannot read. The exact failure is
retained and the corrected v2 uses a repository-relative path.

In v2, the first partial case succeeds:20px is reported
`target_not_reached`, Save does not start and release verifies. The target case
then loses X11 focus immediately after button-down. The owner releases input and
returns `needs_decision` before the postcondition. The v2 driver incorrectly
assumes that every terminal has a postcondition event and raises `StopIteration`.

V3 reverses the order and preserves early terminals as typed failed cases. It
does not alter the authored condition or repeat either v2 allocation.

## V3 result

The exact first Luna patch `[590,367,60,48]` is used without editing.

| Endpoint | Target | Partial |
| --- | ---: | ---: |
| fresh visual displacement | 24px | 20px |
| two anchor samples | 24px,24px | 20px,20px |
| condition | met | target_not_reached |
| later Save started | yes | no |
| saved SVG screen-equivalent x change | 24px | 0px |
| terminal | completed | needs_decision |
| input release verified | yes | yes |
| condition sample span | 100.628ms | 101.891ms |

The two fresh initial images are byte-identical. Exact frame reconstruction and
saved SVG checks pass on Windows and WSL.

## Unchanged replication

A second preregistered pair uses the same canonical first Luna output, the same
allocations and fresh X11 processes. It reverses order to partial then target.
The20px case again stops before Save and the24px case again admits Save. Across
both successful pairs, target is2/2, partial is2/2, all38 exact frames reconstruct
and all four terminals verify release. Initial images are byte-identical across
all four cases. Sample spans are89.946--101.891ms.

The first replication preregistration attempt is retained before input: a byte
hash compared a CRLF checkout with an LF generated file even though canonical
JSON was identical. The corrected allocation binds canonical parsed JSON. The
first audit invocation also expected the older byte-hash field; only the auditor
changed, and both Windows and WSL audits now pass.

## Decision

Promote only as a scoped moved-object local postcondition candidate. Two
opposite-order same-task pairs now show that one previously authored condition
can gate a new process. This does not show a model call inside the live episode,
model-planned pointer motion, new geometry, general object identity, speedup or
token reduction. Placement still requires a different target-and-guard contract.

Primary evidence:

- `results/local-displacement-transfer-01/failure.json`
- `results/local-displacement-transfer-02/failure.json`
- `results/local-displacement-transfer-03/preregistration.json`
- `results/local-displacement-transfer-03/report.json`
- `results/local-displacement-transfer-03/audit.json`
- `results/local-displacement-transfer-04/failure.json`
- `results/local-displacement-transfer-05/preregistration.json`
- `results/local-displacement-transfer-05/report.json`
- `results/local-displacement-transfer-05/audit.json`
