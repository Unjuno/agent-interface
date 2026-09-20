# Primary public API use in Inkscape

Source before diagnostic wording change: 43bd99f86. WSL Ubuntu, one owned
Xvfb allocation at a time, no helper model or sensor. An initial SVG rectangle
x=80,y=80,width=120,height=80 was prepared as a task fixture.

Attempts 1-3 ended before application input: unsupported --new-instance;
window-title timeout; window-class timeout. All owners exited 1 and owned
process cleanup was recorded. Attempt 4 used documented --app-id-tag, explicit
GDK_BACKEND=x11, removed inherited Wayland/DBus addressing, and a longer startup
bound. Multiple conditions changed: this is not a causal startup comparison.
It delivered the actual Inkscape canvas through public observe and review_bytes.

The primary assistant viewed image 1, chose the visible rectangle at (480,370),
and requested a click, three right keys, Save and 100ms rendering allowance.
Uppercase RIGHT was refused with backend_emissions=0 and verified neutral
release. After inspecting that result, the primary authored a new request with
Right. It was not an automatic replay. That program completed and returned its
captured image via public review_bytes; no temporary report is required by that
API, though this harness retains raw responses for audit.

Primary visual inspection of image 3 showed X=84,Y=80,Width=120 and Document
saved. Parsing the saved SVG confirmed x=84,y=80,width=120,height=80. Directional
move/save passed. Nominal three two-unit steps would yield x=86; that exact
expectation failed. Do not equate backend completion with per-key application
acceptance. This run does not identify the cause or justify a default delay.
The primary then requested finish; owner exited 0 and cleanup is retained.

The follow-up implementation only improves unmapped uppercase arrow errors to
include canonical case-sensitive names. It does not change key semantics,
input admission or repeat timing. Focused tests cover the hint/no-emission
boundary; no post-change GUI rerun is claimed for error wording.

This tests the direct public API and received-byte image route, not the separate
guarded target-handle path. Fixed fixture initialization and wrapper lifecycle
are scripted; action decisions above were authored after viewing images.
No matched performance, human baseline, model usage/cost or independent external
auditor. Do not promote it as broad success/reliability evidence. Profile/cache
files are excluded; runtime response/image/program/decision/SVG/cleanup bytes
are retained unchanged. Original paths are historical. Manifest excludes itself.
