# Calc PNG integration decision

**HOLD_DEFAULT_CHANGE.** Shared capture timing found material PNG cost, but the frozen live pair did not show consistent response improvement or equal final visual readiness. Runtime defaults remain unchanged. This result informs #2789; it does not complete overall acceptance.

## Evidence chain

All runs used source 3c057b79b87e9faac967c919adb92f0c4e542499 in WSL. The primary assistant personally viewed screenshots and chose the GUI actions. No helper model, action replay, extra observation or hidden recovery was used. The actual provider configuration/model rendering/input tokens are not attested.

1. `capture-timing-calc-live-01`, seed991299: primary wrote826/141, handled XLSX format confirmation, then independent file evaluation passed. Ten captures, two completed dispatches with verified input release. SDK round trips875.982/847.856ms; nested encode totals219.131/224.413ms. This motivated testing the #4401 compression idea on this route.
2. `calc-png-route-comparison-01`: ten retained frames, three alternating pairs each,60 rows. Exact shared sink versus a one-line `compress_level=1` variant. All decoded pixels equal. Median paired ratios: encode0.740538, local sink/file/base64JSON/decode0.806320, PNGbytes1.151468. No real transport/model in this stage. It passed only the prospective gate for a live comparison.
3. `calc-png-live-pair-01`, seed991300: prospectively frozen baseline then candidate, same497/220 task, two input stages per arm,2ms text gap and250ms waits. Experiment-only executable wrappers load the frozen sink before launching the normal owner; both variants use the same wrapper logic. Loaded source hashes match freeze. Production source and defaults are unchanged.

| Live operation | Standard SDK ms | Level1 SDK ms | Standard PNG bytes | Level1 PNG bytes |
|---|---:|---:|---:|---:|
| Input/save request |737.205|658.893|77003|88599|
| Format confirmation |867.535|992.086|58641|65973|

Both arms independently saved exact497/220. Both used10 captures and two completed dispatches with verified empty input state. Both owner and SDK client processes exited0. Initial and first-response RGB pixels match exactly across arms; final-response pixels do not. The candidate final image shows greyed controls, recorded by the primary before independent evaluation. Do not call this equal visual completion or attribute the difference solely to compression. No extra observation was taken to replace it. The independent file result becomes known later than the final screenshot.

SDK round trips end at the local SDK client; they exclude the host image rendering, primary reasoning and semantic completion endpoint. The pair is sequential, unreplicated, uses a known task, and does not control system load or all desktop state (window inventories differ). PNG size is not model input token count. Encoding and bridge spans are nested and must not be added to total latency. Cleanup proves tracked processes terminal plus later owner exit; it does not prove all descendants cleaned up.

## Integration consequence

Keep standard PNG settings and fresh guard observations. The offline improvement did not justify a default change after live use. Future compression adoption needs repeated counterbalanced live comparisons and comparable useful visual feedback, with transport/model costs measured where available. This is not a reason to weaken readiness checks or select only the faster action. Earlier #4401 HOLD remains unchanged.

The archive includes original requests, replies, images, source freezes, experiment wrappers and analysis results, including the differing final frame. verify.py verifies archive identities, four completed live dispatches/releases, independent evaluations and cross-arm pixel comparisons. Its pixel decoder shares Pillow with the implementation; it is not an independent decoder. Hash verification is evidence integrity, not proof of performance.
