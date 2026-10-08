# Visual tracking development screen, revision 1

Freeze the source bytes before the fresh screen. This is a synthetic GUI motor
study, not a same-model LLM comparison or representative desktop benchmark.

The 800x400 X11 fixture displays a red target following a seeded sine trajectory
and a green player driven by OS Left/Right keys. Real wall time continues while
the controller waits. The controller reads full-screen RGB pixels at nominal
50 ms intervals. It receives no trajectory, velocity, seed or state oracle.
The orchestration process uses the seed to launch the fixture, but the motor
policy only takes detected red/green pixel centers and elapsed cadence time.

Both arms use the same directional policy with an 18 px deadband. Local updates
the held key every observation. Delayed updates every 250 or 1000 ms, keeping
its previous input between updates. This simulates a decision **cadence**, not
in-flight inference delay: each update uses a fresh image, not a delayed one.
Both arms capture on the same nominal schedule. No planner runs in either arm.

Fresh screen: seeds 860201–860203; both cadences; six-second episodes; one fresh
Xvfb/Openbox/application per arm. Alternate arm order by seed/cadence index.
Twelve episodes total. Retain failures and do not silently retry or replace
failed pairs. Initial app-development trials are separate from this screen.

Primary metrics: application-side time-weighted mean absolute horizontal error
and fraction of time within 30 px. Read the oracle only after task input ends.
Also retain controller observations, decisions, loop p95 and release checks.
Every-second screenshots are illustrative samples; no full image-replay or
image/token compression claim. App logs sample at nominal 16 ms with actual
timestamps. Report paired differences and every episode; no broad significance
or human-speed claim from these three seeds.

Initial development attempt timed out before window discovery. A diagnostic
run and unchanged-code retry displayed the window; root cause is unconfirmed.
Revision 1 now observes the public WM readiness property before spawning the
fixture. Do not claim this establishes the cause or fixes all startup races.
