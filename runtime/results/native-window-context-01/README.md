# Native MCP window context across Calc and Inkscape

The native decision schema requires complete window titles for feedback, but
the MCP image response did not expose the existing stage window listing. The
adapter now returns the selected stage's retained `windows-N.json` with its
SHA-256. It performs no new discovery or sensor work, picks no target, and
grants no input authority. Missing, malformed or oversized listings are explicit
without replacing the image or selecting an older listing.

## First result and correction

`native-window-context-01`, source `c42ad645c`, WSL native MCP SDK, seed 991290,
Calc + Inkscape, explicit 2-ms text gaps, 12-stage maximum. The primary assistant
personally viewed each image, supplied each decision and inspected the XLSX
format dialog before confirming it. Four guarded action programs completed
with verified empty input releases. Both saved-file tasks passed.

The first implementation exposed a publication-order defect: all five immediate
continuation responses had `window_inventory.status=unavailable`. The harness
published source/reply before writing the next listing. A later read-only
`native_observe(stage=5)` recovered the already-recorded dialog listing. This
extra call and all five missing-context responses are preserved, not relabelled
as a successful context-delivery result.

The correction moves the already-required listing capture/publication before
its source, and therefore before the stage reply. Each listing is immutable
and written once per stage. The reader adds no sleep, rediscovery or retry.
The real harness-loop tests assert the listing is readable at every source
publication boundary, including observation and refusal branches.

## Fresh corrected use

`native-window-context-02`, source `82b0d0160`, same task seed/application paths
and primary conversation, separate new GUI processes and files. Initial plus
five continuation images all carried recorded window context (6/6). The format
dialog's exact title arrived with its image, so the extra `native_observe` lookup
was unnecessary. No decisions were supplied by another model or a subagent.

Both runs performed the same four guarded actions: move/save the SVG, switch to
Calc, enter/save cells, explicitly confirm XLSX format. Both then received an
explicit no-input finish decision. Each owner and SDK client exited 0; all
tracked children were terminal, with full descendant cleanup unverified.

Persisted files were independently reopened after owner exit:

- Calc: A1=858, A2=326 in the saved XLSX.
- Inkscape: x=54, y=50, width=40, height=30, no transform in the saved SVG.

Program completion and visible cell values were never used as substitutes for
the persisted-state checks. Switching application and closing the dialog
returned `needs_review` feedback; the primary inspected the next image before
continuing. This is expected focus handoff, not permission to replay input.

## Retained scope

The archive contains 313 files from both attempts and the local test run:
requests, complete MCP replies/image blocks, rendered image files, goal/source
records, original missing-context responses, stage listings, release/cleanup,
saved workbook/SVG, readback and SDK timings. Local checks: 176 protocol + 68
harness =244 passed. The final changes after `82b0d0160` add tests/docs/evidence,
not runtime behavior.

Run `python runtime/results/native-window-context-01/verify.py` for read-only
archive hashes, receipt/image/listing linkage, all eight releases, independent
XLSX/XML saved values, terminal owners and the original failure retention.

These are construction allocations, not a randomized performance comparison,
attested model/environment match, registered-host MCP refresh, general desktop
reliability, measured token savings or human-tempo result. The inventory is
historical and not atomic with the image. Each successful context delivery
still requires ordinary observation/binding/input admission. Under #2789 this
improves exact-title and modal handoff usability in the actual desktop path;
overall disposition remains `HOLD_INTEGRATION_INCOMPLETE`.
