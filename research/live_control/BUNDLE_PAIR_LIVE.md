# Registered separate versus bundled GUI pair

The registered AB pair is complete. Both arms save the same correct geometry at
X69.5/Y50/W40/H30. Bundling the identical nine ordered steps reduces submitted
programs from3 to1 and total socket exchanges from9 to5. No new executor, capture
policy or automatic retry was introduced.

| Measure | A: select/edit/save separately | B: one nine-step program |
|---|---:|---:|
| Strict saved geometry | pass | pass |
| Submitted programs | 3 | 1 |
| Socket exchanges including initial/decision/finish | 9 | 5 |
| Archived observations | 16 | 18 |
| Initial capture → GUI decision echo | 57.178 s | 42.748 s |
| Initial capture → final evaluation | 57.525 s | 43.111 s |
| Extra recovery programs | 0 | 0 |

Observed GUI-decision time is14.429 s shorter in B. This single ordered pair does
not establish causal speedup: conversation learning, model configuration and timing
are not independently controlled. B also has a larger result to review at once.
This is evidence for fewer outer boundaries with correct results in this case,
not a general latency, human-speed, token-saving or recovery guarantee.

## Execution and evidence

The protocol was registered in OBSERVATION_COST_PROFILE.md before execution.
`bundle_pair_live_v1.py` runs A then B once each, seed223, target69.5±0.01 with
Y/size constraints. Both source manifests and initial PNG bytes match. The actual
ordered step lists are identical: select(2), edit(5), save(2). The old ready-event
randomized goal field is not the precision task specification.

A views the initial/selected/edited/saved images and receives three full program
receipts with state tables. B views initial and final images and receives one full
program receipt with all17 state-table observation rows. No extra raw-state dump
is requested. Both record GUI-only geometry decisions, with hashes echoed by runtime
clock commands before finish/evaluation. No saved SVG is inspected before decisions.
No failures, interruptions or recoveries occur in this pair. Both bridge handles
return exit0; independent per-child cleanup inventory remains unavailable.

All captures remain in the runtime archive. B's18 frames versus A's16 arise from
actual settle sampling differences, not a capture-saving policy. Setup readiness
also differs (4 versus2 setup captures), even with equal initial PNGs. The pair
does not make process state or entire execution trajectories identical.

`audit_bundle_pair_v1.py` verifies all14 socket exchanges against132 events,
34 exact PNG/AIT frames, manifests, ordered steps, regenerated receipts and state
tables, owner releases, decision hashes/images and pre-evaluation ordering. It
independently scores the saved SVG using the predeclared tolerance. Both final SVG
hashes match. The scorer covers one direct untransformed rectangle, not arbitrary
document equivalence. First useful model feedback/receipt time and actual model
tokens are not separately instrumented; capture timestamps cannot substitute for
those metrics.

The audit output is exclusive at `results/bundle-pair-01/audit.json`:

```sh
python3 research/live_control/audit_bundle_pair_v1.py
```

## Decision and remaining checks

The pair supports pursuing existing bounded multi-step execution for tasks where
the next steps can be declared from the current evidence. It does not support
blindly bundling across unknown dialogs or failed selections. A can intervene at
two additional boundaries; B cannot recover that opportunity by keeping archives.
The ordinary owner/lease machinery is unchanged, but its behavior during a new
longer bundled program still needs a real focus/error interruption test.

Next verify that the bundled tail stops and input releases during a real focus
fault, then examine another desktop domain/layout with a genuine conditional
boundary. Do not add repeated normal Inkscape pairs merely to improve the timing
headline. Defaults and Research Freeze remain unchanged. Preserve this ordered
pair as exploratory evidence, including its larger B observation count.
