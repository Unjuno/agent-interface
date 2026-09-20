# Primary Calc use of integrated formula text

Fresh private WSL/Xvfb allocation on 2026-09-21, after the formula-text candidate
for #3668. The predecessor's refusal and key-chord workaround remain in #3667.

Candidate source: `a01652410bb49b44cd610b123dfe728f5f530829`.
Portable archive SHA-256:
`61ca858aa78b1db40974709c2bce431f6abaf3162d8011d60725c6d8cd15e468`.
The same code was subsequently merged through #3670. The packaged public MCP
ran from `/tmp` without repository PYTHONPATH; the primary assistant reviewed
saved screenshots and authored subsequent requests through one SDK connection.

## Task and result

Create Quantity / Unit price / Total headers, enter A2=7 and B2=13, enter C2 as
the text `=B2*A2`, and save. The final screen displays 91. Independent parsing
of saved `invoice.fods` finds values 7, 13, 91 and formula `of:=[.B2]*[.A2]`.
The public dispatch request contains the formula as one `text` operation with
`gap_ms: 20`, not a layout-specific sequence of formula key chords.

Two explicit observations and two dispatches were used: initial whole-screen
observation, close the visible startup tip, enter/save the sheet, then an explicit
final observation. Both input dispatches completed. The formula dispatch reports
verified release and no recovery required. The initial post-input capture still
showed editing/saving; semantic completion was determined from the final image
and independently checked against the saved document. No input was replayed.

The primary assistant then requested finish. Owner exit was 0; tracked Xvfb,
Openbox and LibreOffice launchers were reaped. Captured process-group member paths
were absent after cleanup. The retained harness still declares
`descendants_verified: false`; exhaustive descendant closure is not established.

## Evidence and scope

All 42 allocation files are retained in `evidence.tar.gz`: harness/task source,
initial and saved documents, explicit decisions, actual requests with leases,
MCP replies, PNGs, raw reports, process logs and cleanup. Every archived member
was reread and matched to `manifest.json`; `archive.json` identifies the bundle.

This is a new-data functional transfer of bounded text support, not a matched
performance comparison. The initial whole-screen observation also differs from
the predecessor's window-client view, so call-count differences are not a causal
efficiency result. No sensor, subagent, additional model or automatic retry was
used. Source/binding remain caller assertions; the private harness gives each
explicit decision a 10-second host-monotonic lease. The public server does not
issue that authority.

WSL saved-file/view-tool delivery does not establish direct host-presentation,
model usage/cost, human-tempo latency, arbitrary layouts/Unicode, or formal
container acceptance. Broader #3352/#3370 gates remain open.
