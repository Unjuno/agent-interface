# Issue #5865 T1 producer construction pilot

This is a construction-only pilot for the producer gate proposed in [Issue #5865](https://github.com/Unjuno/agent-interface/issues/5865). It is not the formal T1 held-out run. The original T0 negative-search classifier was not present in current `main`, open PR #8136, or the available local worktrees, so the required unchanged-T0-classifier gate could not be met. Do not cite this package as T1 or as an application-transfer result.

## H/T/D/C/U

**H:** A versioned complete inventory for a bounded stable-control surface can support scoped negative evidence; a viewport-only producer for a virtualized/canvas-like surface should abstain, including when a matching object exists outside the rendered viewport.

**T:** Construction tests exercise complete same-epoch paging, missing and duplicate pages, duplicate identities, epoch/surface drift, missing writer coverage, and an in-scope positive. A separately invoked candidate consumes only `candidate_input.json`; the independent auditor joins its output with the separate `oracle_truth.json`. A local synthetic browser fixture was also inspected with Codex CUA for accessible stable controls and a canvas list that renders rows 0–5 while the independently modeled target at row 17 is not visible.

**D:** Construction gate: zero false/unsupported negative certificates in the independent audit; report coverage by surface. Pilot-derived threshold proposal: at least 80% useful coverage on held-out stable-control negative requests. Virtualized/canvas coverage is reported separately and does not inherit the stable-control threshold.

**C:** Producer metadata can be wrong or omit a writer. The classifier cannot establish the truth of its producer's completeness assertion; only the isolated application-side oracle detected truth. A hand-authored finite fixture may be easier than a real app's native tree or application-state source.

**U:** Synthetic browser fixture and finite authored inputs only. No native GUI, accessibility API, real application, user task, latency, task effect, action authority, or product benefit was tested. The historical T0 classifier was unavailable, so formal T1 remains gated.

## Executed construction pilot

Allocation `T1-CONSTRUCTION-PILOT-20261005` used 12 fixed cases. The candidate ran once (`python3 run_candidate.py`) and emitted 12 rows. The independent auditor ran once (`python3 audit_pilot.py`) against separate oracle truth and returned `PASS_AUDIT`, 0 audit errors, and 0 false negatives. It certified 5/8 oracle-eligible negative requests: 5/5 stable controls, 0/2 virtualized no-match requests, and 0/1 mutation no-match request. Overall useful coverage was 62.5%; the remaining eligible cases correctly abstained because producer coverage was not established. A stable positive control returned a match. A below-viewport matching target did not produce a negative certificate.

This pilot motivated a prospective 80% stable-control held-out threshold, allowing at most one abstention per five eligible stable requests in the threshold illustration. It is a threshold estimate from five pilot requests, not a calibrated population threshold. The threshold is recorded before any held-out run in `threshold_pilot.json`; the actual formal run remains gated on recovering and pinning the unchanged T0 classifier and completing a fresh protocol review.

## GUI observation

`fixture.html` was opened in the Codex in-app browser and observed with CUA. Its accessibility tree exposes four stable buttons, while the canvas-like list exposes only the description “Rows 0 through 5 of a virtualized 30-row list.” The CUA screenshot showed only rows 0–5; the “Delete” target at row 17 was absent from the visible canvas. The verbatim observation summary and limits are in `ui_observation.json`. The screenshot was not exported to a separate file.

## Reproduction and retained evidence

From this directory:

```sh
python3 -m unittest -v
python3 run_candidate.py
python3 audit_pilot.py
```

The commands above include construction tests and the single pilot invocation pair. Do not rerun the pilot allocation as a formal experiment. Candidate input, oracle truth, candidate output, audit output, threshold decision, and CUA notes are retained here. SHA-256 identities for the pilot source and outputs are recorded in `threshold_pilot.json`.
