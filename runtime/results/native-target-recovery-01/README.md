# Live target refusal recovery

Primary-assistant WSL Inkscape run on source 72aa7b1d0, seed 991123,
max_stages 2, text_gap_ms 0. One allocation; no application restart or input replay.

The primary viewed the startup image and submitted the same flat-center
click/move/save/finish_after decision as the previous failure. Target minting
refused it before input. This time the response contained a fresh sequence-2
image, target_refusal with input_dispatched=false and finish_after_applied=false,
and a next-stage continuation. The primary viewed this image and chose a new
point [600,378] near the red rectangle edge. The second request moved right and
saved. Its final screenshot showed X60/Y50/W40/H30 and document-saved status;
the saved SVG passed task evaluation. One input program executed. The tracked
cleanup completed, owner PID21413 exited 0, and relay EOF exited 0.

Four MCP calls: start, refused-target submit, corrected submit, status. The
refusal consumes stage 1 and the corrected request consumes stage 2. No automatic
correction, extra allocation, sensor or delegated model was used. UI semantics
above were reviewed by the primary; audit.py checks retained byte/geometry and
protocol facts, not screenshot semantics.

The initial request and startup PNG match native-validation-recovery-01 exactly.
That earlier run exited on target refusal; this run returned a new decision
boundary and finished after a new primary-authored request. Code and conversation
context differ: this demonstrates a scoped recovery path, not a controlled
latency, model-token, human-speed or general success-rate improvement. Formal
container/independent-adoption gates remain unverified. Manifest excludes itself.
