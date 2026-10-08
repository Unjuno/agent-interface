# Native observation review: actual Calc self-use

2026-09-20. Existing `agent_review.py --native` now presents a native bridge
observation or explicit feedback/window-review observation in the same response
as its exact PNG. It retains the complete native report, report hash, sequence,
binding revision, capture identity and image hash. There is no capture, focus,
input, authority grant, freshness renewal, or inferred task success in this
presentation helper. Existing event-receipt review remains unchanged.

The primary assistant viewed sequences 1, 7 and 12 through this CLI and rendered
the returned MCP image block directly. It grounded the Calc name box at (18,108),
entered 116 and 476 using the existing 2 ms text policy, then viewed and clicked
Use Excel format at (785,462). It viewed the final sheet and explicitly finished.
Two native programs completed; the independent workbook check found [116,476].
All three reviewed frames are the exact native captures, with no Windows path
conversion or separate file-image read. No matched speedup or fewer total task
turns is claimed; the harness still requires decision submission and waiting.
Primary-model input tokens/cost were unavailable; helper-model calls were zero.

The modal-close feedback still records BadWindow/needs_review. The subsequent
explicit window review supplies the next source; presentation does not relabel
the earlier failure. Missing feedback images do not fall back to an older source.
Hash/link mismatches retain the receipt but render no image. Nine focused tests
passed. All 12 bridge image links and the saved workbook were independently read
in the retention script. Cleanup records terminal processes, not clean exit of
every application descendant.

`run/` preserves raw live files, images, decisions, results and saved workbook.
`review-*.json` are read-only post-run replays of the same reports, with base64
omitted; they are not original timed transport logs. Actual viewing occurred in
the assistant conversation before each decision. `source/` retains the executed
review/helper/harness source. SHA256.json covers retained data except this README.
Absolute runtime paths remain original; retained image copies are under
run/bridge/images and must not be represented as a new observation.

An initial launch without PYTHONPATH failed with ModuleNotFoundError: runtime,
before harness setup or input. The corrected launch used PYTHONPATH=.:research/live_control.
That shell traceback is in the conversation, not a retained runtime attempt.

This joins the existing review presenter to the experimental native path. It
is not a promoted persistent transport, semantic effect detector, or complete
single-call action/result/image interface. Base commit:
14ca670c49d8b2144c4e0104d92526e394f0d02a.
