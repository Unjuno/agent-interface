# Compact receipt use across two real applications

On runtime871e3c784dc4e59c639b89f63258b2289073fbdf, the primary agent used
`compact=true, report_refs=true` for every observe/dispatch call in one private
Linux/Xvfb/Openbox Calc/Inkscape session. The driver saved all requests, responses
and images; the primary inspected images and selected subsequent operations.
Management calls retained their existing format. No server default changed.

The trial made16 public calls, returned15 primary-reviewed images and11 v3
receipts. The primary read activation details directly from
`receipt.source.raw_report.result.execution.activations`. Final saved workbook
values were548/478; the saved SVG rectangle was[56,50,40,30], without a transform.
Explicit close verified empty held keys/buttons. Runner exit0; fixture cleanup
returned normally. File scoring followed primary visual review and close.

This was not failure-free: initial text477 displayed47, including in a fresh
inspection. The primary explicitly selected the cell, entered477 with50ms gaps
and saved, then confirmed477 visually before switching apps. Final478 was also
entered with gaps. This preserves one extra recovery dispatch, not evidence for
the cause of the missing character, a universal50ms setting, or a compression
effect. The successful operation receipt did not establish correct text.

An earlier offline replay used10 observe/dispatch reports from the retained
activation-primary02 trial (five management calls excluded). Serialized text
excluding image blocks totaled53,599 UTF-8 bytes for full and compact-only
presentation, versus37,470 with report references:30.09% less. Expanded receipts,
outcome summaries and image blocks matched. This is not whole-session traffic,
provider tokens, cost or latency. The live compact trial uses a different seed
and includes recovery, so it is not a matched performance comparison.

The primary interacted through SDK-driver summaries, image tools and local file
reads. This mediation is explicitly outside any claim about direct host model
token use or cognitive benefit. No model usage/cost/latency counters were
available; those fields remain null. Decision: retain the explicit opt-in for
clients that understand v3; keep defaults and images unchanged.

`raw.tar.gz` includes the live trial (including wrong-text images), offline
replay script/results and per-file manifests. Original source reports for the
offline replay are in
[the activation bundle](../explicit-window-activation-01/README.md).
Run `python runtime/results/compact-mixed-app-01/verify.py` with openpyxl to check
the archive, v3 expansion, request options, image forwarding, session continuity,
saved files and close. It does not independently judge the screenshots or
recompute provider token savings.
