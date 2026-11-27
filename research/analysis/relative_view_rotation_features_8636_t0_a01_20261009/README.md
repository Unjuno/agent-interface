# Issue #8636 T0 A01: rotation-invariant image features for relative-view control

This additive package tests one finite synthetic view-alignment task. It compares raw normalized image-point coordinates, a three-bearing spherical feature contract, and a hidden-pose oracle upper reference. It uses deterministic PPM landmark frames and relative yaw/pitch actions; no model, GUI, game, OS input, GPU, container, shared VM, or external effect is used.

The result applies only to the frozen synthetic fixture and its stated feature/actuator model. It does not establish camera-pose recovery, actual GUI/game control, task effect, application safety, latency or token benefit, or general portability. Read `PROTOCOL.md`, `FREEZE.json`, and `REPORT.md` together; raw frames and exact first outputs are under `results/first-outcome/`.
