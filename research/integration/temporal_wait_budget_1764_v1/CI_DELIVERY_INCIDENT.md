# Publication-trigger incident and engineering repair — PR #4071

Opening this evidence-only PR triggered three legacy GTK allocation workflows
because their PR path filters covered research/integration/** and runtime/**.
The author failed to inspect these triggers before publication. GitHub MCP exposed
no cancel operation; the PR was converted to Draft, which did not cancel runs.
No alternate endpoint was used to bypass that tooling limit.

## Actual observed execution (not new scientific evidence)

| Workflow | Run | Artifact | ZIP SHA-256 |
|---|---|---|---|
| 2606 v1 | 35666723259 | 10669418205 | 00528aa055453402eed44f695248018a4f2fbfe85f329023392ae88a1e338cd5 |
| 2836 | 35666723305 | 10669113301 | 58a51aeee8f96ddb33ba3d3b66b5e6a46258e82b1d884cc0ce68826c002dca78 |
| 2851 Xlib | 35666723270 | 10669173371 | 4c3d5151bfb9429627c110f8fc69cd5ab98218d80d69a34fd1a5111cfc32f29d |

All downloaded ZIP hashes match GitHub artifact digests. Each retained eight
rows and runner exit 0. Executed source-commit.txt is GitHub's PR test-merge
commit a33972224aece74ace26b3937211f75217a8521f, not the temporal freeze.
Runs 2606/2836 record Xlib-unavailable dispatch refusals and no native emissions.
Run 2851 records four completed native-program rows and 106 total emissions;
those four formal receipts report release_verified=true. These are inspected raw
fields, not an independent GTK effect/release audit or a safety certification.
The CI container is not the user's desktop. No zero-remote-GUI claim is made.

Disposition: UNPLANNED_LEGACY_CI_EXECUTION_RETAINED_UNSCORED. All 24 rows are
excluded from temporal evidence and historical scientific promotion. Existing
workflow wrappers exit 0 after recording outcomes, so a green workflow is not
a scientific PASS. None was manually dispatched or retried in this continuation.
No original temporal or older GTK result was overwritten or pooled.

## Minimal repair and scope expansion

Only the on blocks of gtk-formal-allocation-2606-v1.yml,
gtk-bounded-allocation-2836.yml and gtk-xlib-allocation-2851.yml change to
workflow_dispatch. Each entire jobs block is byte-identical to the source read
before repair, with SHA-256 binding in CI_TRIGGER_VALIDATION.json. Their manual
execution still requires the existing separately authorized allocation contract;
the repair does not authorize repeating a consumed allocation.

A new Legacy GTK dispatch contract workflow runs only a standard-library source
regression on PR/push changes to these definitions and its own test. It builds no
image and invokes no experiment. Eight tests accept the exact manual templates,
reject PR/push/extra/missing triggers, and detect job-body changes. An independent
local YAML parser confirms event keys and unchanged jobs. Existing ordinary
MAP01 scorer replay and other checks remain enabled; no failing science is hidden.
Targeted open-Issue and open-PR searches found no competing trigger repair, but
unpublished work is unknown. The new shared-file scope was announced on this PR
before the repair. No wrapper-successor Issue was created.

## Raw retention and audit-only access

ci_incident/CAPSULE.json plus two ordered binary parts retain every member of
all three downloaded artifacts byte-for-byte, the three original workflow
sources, the raw-field inspection and the before/after source binding. This is
99 files / 158208 member bytes. Original ZIP container bytes remain in the
conversation downloads; the capsule preserves member bytes, not ZIP encoding.

```sh
python -I -S -B ci_incident/restore.py /tmp/pr4071-ci-incident
python3 -B .github/scripts/test_legacy_gtk_manual_dispatch.py -v
```

Run the second command from repository root. The first command restores data
only. Do not invoke the retained legacy runners to recheck this incident.
The original temporal 163-file capsule and frozen audit remain unchanged.
