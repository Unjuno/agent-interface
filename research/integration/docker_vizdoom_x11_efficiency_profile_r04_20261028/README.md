# Current-main Docker/Xvfb efficiency profile R04

R04 added in-path timing around the guarded bridge save method, compiled
adapter retention, perception callback and effect-verifier callback. It used
four new counterbalanced pairs and the same one-action 600 ms W-forward
ViZDoom FreeDoom MAP01 task. All 8 arms passed task-effect and input-release
gates; all Docker commands exited 0. The pinned image and read-only/no-network
container conditions are in the task-local packet.

| Pair | Direct route | Compiled route | Compiled minus direct |
|---:|---:|---:|---:|
| 19 | 866.050 ms | 957.390 ms | +91.340 ms |
| 20 | 882.710 ms | 929.290 ms | +46.580 ms |
| 21 | 880.360 ms | 923.310 ms | +42.950 ms |
| 22 | 875.770 ms | 911.040 ms | +35.270 ms |

Mean route latency was 876.222 ms direct and 930.256 ms compiled, a compiled
increase of 54.034 ms (+6.17%). This instrumented result is not pooled with
R03 and may include timing-wrapper overhead.

The execution interval averaged 693.089 ms direct and 696.513 ms compiled
(+3.424 ms). In-route `_save` time averaged 31.695 ms direct and 84.285 ms
compiled. Compiled retained 19 additional receipt files per arm; their saver
calls averaged 49.535 ms. The inclusive `compiled._Adapter.retain` measurement
was 49.837 ms, including those nested saves. Both routes ended at bridge
sequence 7 per arm.

These records make receipt persistence the strongest profiling lead: the
additional saves occurred on the timed route and their measured duration is
near the route delta. They do not prove that writes alone caused the difference.
Some saves overlap the bridge execution interval, and the profile does not
separately isolate every graph transition, guard check, serialization and
callback. Retain per-transition evidence and its failure/replay semantics
while investigating any performance change.

The raw runner, exact conditions, per-arm receipts, syntax-check attempt,
wrapper exits and hashes remain in
`private-packets/docker_vizdoom_x11_efficiency_profile_currentmain_20261028_r04/`.
The original preregistration Markdown has a disclosed interpolation/escaping
defect; exact structured conditions and runner digest remain in JSON. See the
packet erratum before using it as preregistered evidence.
