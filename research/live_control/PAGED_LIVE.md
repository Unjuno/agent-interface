# First live use of line-aware pages — audited

Fresh private Inkscape seed 205 ran through unchanged v9 pointer runtime. The new
`paged_live_v1.py` explicitly issued one move-right/save program after initial
image review. It persisted the original report and reversible view, returning the
first line-aware v2 page plus the selected original image. Six separate read-only
CLI calls delivered remaining pages. All seven pages and both original images were
visibly reviewed before finish; no black image, text truncation or input retry was
observed. This is one known-fixture integration episode, not a paired speed study.

Independent evaluation passed with rectangle x52, y50, width40, height30, no
transform. The bridge exited 0. Runtime receipts contain 31 events; the report view
is 23,777 bytes. Finish verifies saved pages reconstruct the view exactly, while
explicitly disclaiming that file existence proves model review. The completed audit
verifies pinned sources, all 31 raw events against four socket exchanges, eight exact
decoded frames (including reused PNGs), seven-page reconstruction, and independent
SVG task result. Evidence is archived in `results/paged-live-01`; preserve this
episode rather than rerunning it. Run `python3 research/live_control/audit_paged_live_v1.py`.

| Measurement | Value |
| --- | ---: |
| View source bytes / total page wire bytes | 23,777 / 28,390 |
| Additional page CLI calls | 6 |
| Initial capture to terminal | 25.581753 s |
| Initial capture to independent evaluation | 95.544143 s |
| Terminal to independent evaluation | 69.962389 s |
| First report reply to last page CLI return | 56.144528 s |

These intervals include orchestration, model review and commentary; they do not
isolate pager CPU overhead or model receipt. Bridge exit 0 was observed, but the
old Inkscape fixture has no structured per-child cleanup report.

The 4096-byte guarantee applies to serialized page objects, not the enclosing
move response plus image/notice. Initial and finish responses use ordinary fixture
receipts. This integration does not implement a universal tool-output cap.

Observed cost: one simple task result needed seven pages/six additional CLI calls.
Full-history review remained cumbersome despite line boundaries. Decision: keep
paging as an explicit recovery/detail path, not the mandatory normal interaction
flow. Next define a compact decision receipt with explicit links to full evidence,
separate program status from task success, include interruptions/errors and evidence
coverage, and surface unsupported/unknown events as requiring further review.
Do not rename partial evidence as full review or silently drop exceptional records.
Validate against retained interrupted/overflow cases before a fresh live comparison.
No model token accounting, receipt timestamps, human-speed qualification or
black-image repair is demonstrated here.
