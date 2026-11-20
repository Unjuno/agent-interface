# A03 audit-only protocol

Issue: #7933; parent candidate evidence: #7926.
Allocation: V39-V15-PREPOST-A03-AUDIT-20261005-01.
Scope: independent raw-only audit of the frozen A02 fake-X output. No candidate/runtime invocation; exactly one auditor invocation; zero retries.

## Frozen parent inputs
- A02 candidate stdout: Git blob 7878e4e6aba0fe7d085f6a1e41192ef120d8b20d; SHA-256 0336cfa2eeebbe48ad816168d5466938a936fcf0782211b21847df6c20038596.
- A02 PRE-RUN: Git blob d495956797c541f5bf6680ae31c87ce2d2d5ff00; SHA-256 98581f50e8ccb3e3914aca454975e4dcd523575acf09023e42971dd1b3ce13e7.
- A02 original AUDIT: Git blob c7f355b41c95f62c5495dcc94e53b3283ea83aa7; SHA-256 9e44c3a1cfb34715ebcb551cf59fac35961afbf6363d9c31fbf648c541614ce2.

The invocation must map those exact three named files to auditor arguments; do not substitute this A03 PRE-RUN for the parent A02 PRE-RUN.

## Gate
Check admission events separately from release-transition events. Independently recompute per-key classifications from sampled keycodes. Verify normal case has no post-sample held key and completes close; lost-SPACE case suppresses SPACE UP, retains keycode 65 at post-sample, classifies it STILL_DOWN_AT_POST_SAMPLE, and fails terminal close while retaining 65. Verify the A02 audit-v1 failure is historical evidence only. Run seven mutation controls. The auditor exit and full stdout are retained without retry.

## Runtime
Docker was attempted but cannot read local containerd content-store blobs (operation not supported); do not claim a container run. Use the preregistered host Python standard-library fallback only. No real X11, physical input, application effect, gameplay, useful feedback, latency, recovery efficacy, or threat-control claim is in scope.
