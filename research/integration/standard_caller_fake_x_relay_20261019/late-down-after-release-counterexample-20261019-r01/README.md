# Fake X late-request-after-readback counterexample

This packet adds one composed standard-caller policy check to the existing
Fake X relay fixtures. Against main `168200eb43dd0f9144b3ed4aef551387674c7bfd`
and this checkout's additive test change, the test holds a synthetic old-owner
KeyPress in a server queue, injects disconnect and a separate empty release
readback, then delivers the queued KeyPress after that readback. The public
caller and terminal record must remain `UNKNOWN`, keep `release_confirmed=false`,
deny replay, and report `task_success=null`.

The event indexes preserve the modeled order. The host's `monotonic_ns` clock
returned the same value for successive events in the first attempt, so the
test does not use timestamp ordering as a substitute for protocol ordering.
That failed assertion and the successful normal/optimized runs are retained in
[`raw/`](raw/); the first attempt is a harness-resolution counterexample, not a
product failure.

After adding the regression, the full
`runtime.cli_v1.test_mcp_relay_composition` module passed 3/3 tests normally and
3/3 under `-O` on the same host. Exact module output is included in the packet
hashes. The regression source was `git hash-object`
`ea1969e67ba8576a918fbcbc5158d2747d6851fa` at the recorded run.

The broader relevant suites also passed after the change: owner/process,
relay-composition, and XRes-fence passed 40/40 normally and 40/40 under `-O`;
offline parser, relay, and composition passed 30/30 in both modes. These suites
reuse the same composition module and are validation, not additional independent
experiments.

This is a deterministic policy counterexample with a synthetic queue and
injected disconnect/readback. The protocol ordering is modeled, not observed
from a live X server. It proves no X server queue fence, physical key-up,
bounded physical release, supported-application task effect, MAP01 outcome,
or general recovery. It consumes no WSLc allocation and uses no Xvfb, desktop
input, or live experiment.

The full conditions are in [`conditions.json`](conditions.json); raw records and
test output are listed with SHA-256 digests in [`SHA256SUMS`](SHA256SUMS).
