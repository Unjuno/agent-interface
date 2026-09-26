# Exact-title feedback: primary WSL use

The Native MCP discovery previously described expected_title without saying it
was exact equality. In primary run01 the caller supplied `shape.svg` although
the actual title was `shape.svg - Inkscape`. Existing feedback waited to its
2000ms deadline and returned pending. The guidance now specifies the complete,
case-sensitive title, including the application suffix. No matching, sensor,
timeout, admission or execution implementation changed.

A fresh primary run02 used the displayed full title. Both runs used WSL Ubuntu,
Inkscape1.2.2, MCP1.30.0, seed991284, text gap2ms, private Xvfb, an explicit
input-free observe followed by one input request: click598,390, Right repeat3,
Ctrl+S and wait250ms. The initial and refreshed images were viewed before input.
Only expected_title differs in the submitted action arguments. Both primary
visual declarations preceded finish/evaluator and separate saved-file parsing.
The saved SVG bytes are identical: x54/y50/width40/height30/transform absent.
Input release was verified; owner and client exited0. Full descendant cleanup
remains unverified. No helper agent, sensor change or automatic replay was used.

| Recorded measurement | run01 | run02 |
| --- | ---: | ---: |
| Feedback result | pending | matched |
| Feedback samples | 40 | 1 |
| Feedback including capture, ms | 2070.657 | 101.428 |
| Input SDK call, ms | 2945.577 | 1124.780 |
| First observe through finish return, s | 73.237 | 125.997 |

The title mismatch explains the old feedback deadline path; the successor
exercised the existing match path. The total client span worsened. This is an
ordered pair, not a randomized/repeated performance study. WSL program versions
match, but the allocations are separate and clock origins differ; no cross-run
timestamp subtraction is valid. Scheduling, host tools and primary deliberation
are uncontrolled. Model identity/configuration are not independently retained;
no matched-model benchmark, token reduction or human-speed claim is established.
Title matching is an application cue, never proof of durable task completion.

Source recorded before use: run01 4d3cb6adc32877cc4b270bf1c186173982553a21;
run02 e06d29cc2 (full revision in archive). No runtime source edits occurred
while either allocation was live. This is SDK-mediated use, not host-registered
MCP. The guidance commit passed the existing native MCP/bridge suites: 30 tests
in6.729s on WSL. That test output is in the session transcript, not this archive.

The archive includes all176 files from the two completed allocation directories,
including their client scripts, requests, responses, images, saved files and
environment inventories. run01's earlier manifest covers its own89 files;
the outer manifest covers both directories. The predecessor Docker refusal
remains separately frozen in native-desktop-continuation-01 and is not upgraded.

Run `python runtime/results/native-exact-title-01/verify.py` for a read-only
archive hash and outcome consistency check. It does not replay input or
independently validate all pixels, performance or the six-task integration gate.
