# Actual browser self-use with client phase endpoints

The assistant used optional runtime v28/socket v12/client v6 against the same
known prefilled browser fixture and seed 991029. It viewed initial image 001.png,
navigated to the fixture URL, viewed the returned observation reference 006.png
(sequence 10), then selected the existing old-draft-42 text and replaced it with
t991029 before submitting. Steps were chosen after those image observations.
This is a simple known fixture, not an unseen recovery challenge or scripted probe.

The independent server evaluation records exactly value=t991029. Two admitted
programs completed with verified input release, and all 13 frames reconstructed
exactly. Request lineage, program preparation replay and the entire delivered
prefix agree. Direct final evaluation skipped the optional drain, so there were
three socket exchanges before cleanup. The server exited successfully after finish.

## Timing evidence

Both caller sidecars contain 15 ordered endpoints with the same explicit clock
domain as all runtime events. All model endpoints remain null.

| Interval | Navigate | Replace and submit |
|---|---:|---:|
| Main entry to local stdout flush return | 992.360 ms | 458.674 ms |
| Source loaded to program prepared | 6.854 ms | 12.003 ms |
| Program prepared to request persisted | 9.383 ms | 9.569 ms |
| sendall return to complete response line | 940.006 ms | 406.528 ms |
| Decode complete to result/image processed | 19.730 ms | 18.410 ms |
| Runtime admission to terminal | 904.765 ms | 361.917 ms |

Form-client stdout flush return to the next client's main entry was 22003.308 ms.
It includes outer tool execution, image inspection, assistant work and process
startup, with no per-component attribution. It is not a measured model thinking
duration. First runtime capture to final client stdout flush return was 72672.036
ms; this also includes initial setup/read orchestration after capture. Stdout flush
is a local pipe endpoint, not model receipt or task understanding.

The previous scripted Calc run's 57.686 ms preparation sample does not recur here
(12.003 ms for submission). Different task, data and scheduling prohibit a storage
or instrumentation causal claim. The outer 22-second boundary is much larger than
the measured local preparation/persistence intervals. Next test combining a
received image's display with its send/wait tool result, using its validated path,
to remove a separate model/tool turn before image inspection. Do not bypass visual
decisions, persistence, admission checks or scoring to make timing look better.

The first launch used unsupported --app browser and exited with argparse status 1.
The corrected --app chromium launch created this session; no input program ran
in the failed launch. launch-failure.json retains that observed setup mistake.
The end-to-end capture metric starts after this failed attempt, so it does not
include that setup cost. No claim of overall workflow speedup is made.

Evidence: results/endpoints-browser-self-use-01 and
results/endpoints-browser-self-use-audit.json; audit_endpoints_browser_self_use.py
checks artifacts and freezes source hashes. Actual model tokens/cost, matched
speedup, instrumentation overhead and human tempo remain unmeasured. Keep all
versions optional and preserve the preceding frozen runs.
