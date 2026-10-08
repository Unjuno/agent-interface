# Actual use of read-only pending-clock recovery

The assistant used the pending-clock reader in a fresh private Inkscape episode.
After viewing the initial rectangle, it deliberately advanced observation and
reused the initial batch in one scripted fault-setup call. The stale attempt
returned an old clock boundary and stopped before submitting its Right hold.
The assistant then invoked `read_pending_clock_v1.run`, received the assembled
history and sequence-2 original image in the same tool response, reviewed them,
and explicitly submitted a new move/save program through the unchanged view caller.

The task passed its legacy rightward-motion contract: saved SVG x=52, y=50,
width=40, height=30, no transform. It does not prove precise requested displacement.
There was no malformed-key retry in this episode. Only the observe setup and
explicit move/save program were admitted; the reader itself issued one read-only
request with no command. It did not submit or repeat any input.

## Evidence and timing

`results/pending-clock-live-01` retains a pre-launch caller source manifest,
runtime source hashes, requests/replies, original and reversible reports, reader
history, selected image and timing, saved SVG and all runtime diagnostics.
The audit verifies eight exact AIT/PNG frames, all 40 unique events covered by
received slices including historical overlap, reader assembly, the exact assembled
batch used by the later caller, the image hash, admitted programs and verified
release, and saved XML against independent evaluation. The bridge exited zero;
the older entry still lacks structured per-child cleanup evidence.

- Eight socket exchanges, including one read-only recovery exchange.
- Five task orchestration calls: initial, combined deliberate fault setup,
  reader/history/image, move/save/image, finish with bridge polling.
- Reader plus local report persistence: **20.181804 ms**.
- Initial capture to independent evaluation: **75.753252374 seconds**.

The local interval excludes shell startup, image selection/presentation and model
review. Most end-to-end time is outside that interval; a fast local read does not
establish human-like control tempo. The tool response still repeats records in
the raw read and assembled history, so general output-budget robustness remains
open. No visible truncation occurred in this episode.

The combined history/image experience and outer-call count are reported from the
conversation in `presentation.json`; runtime logs do not measure model receipt.
Actual model input tokens, costs and receipt timestamps remain null. Compared
with the prior manual-recovery episode, this run has different setup grouping,
no key-schema mistake and different review delays. Do not interpret its shorter
total time as a matched performance effect.

## Next research decision

The reader has now been used after a real stale boundary and before a successful
task. That establishes one integration result. Gap/timeout/interleaving cases
remain recorded-data controls rather than live recovery qualification. Before
adding more local mechanisms, compare a predeclared fixed task/interaction sequence
with and without the helper, retaining full outer-call boundaries and errors.
Separate deterministic transport measurements from actual model-use measurements;
neither substitutes for the other. Domain coverage, correctness and actual
waiting/feedback costs remain the selection criteria.

```sh
python3 research/live_control/audit_pending_clock_live_v1.py
```
