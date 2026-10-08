# Retained inference-gap timing budget v1

Decision: **PASS_RETAINED_INFERENCE_GAP_TIMING_SCALE_SCOPED**

Source-first retained-evidence analysis. Formal invocations: **1**. Reruns/replacements/tuning: **0**. Independent audit: **PASS**, errors `[]`.

## Frozen inputs

- #1451: 10 exact retained requested-route `stdin_closed -> exit` intervals; minimum **9989.1436 ms**. Requested route was `gpt-6-astra` / `medium`, but served identity was not observed/verified.
- #1451 retained T1 maximum useful-effect latency: **2.692318 ms**.
- #1459 retained receipt-drain maximum: **5.182661 ms** (p95 **2.420469 ms**) in the same-host subprocess actuator model.
- #1467 publication caveat is mandatory: #1459's declared raw publication bundle is incomplete; formal parts03..06 are absent. This analysis consumes integrated summary/audit values only and does not reconstruct or rerun #1459.

## Result

Conservative local-boundary allowance:

`B = 2.692318 + 5.182661 = 7.874979 ms`.

Across all ten retained frontier-gap records:

- minimum `gap / B`: **1268.466061941245**;
- maximum `B / gap`: **0.000788353768385** = **0.0788353768385%**;
- minimum descriptive `gap - B`: **9981.268621 ms**;
- candidate/oracle mismatch: **0**;
- five directed corruption/schema controls: **5/5 expected dispositions**.

The preregistered gates (`gap/B >= 100`, overhead `<1%`, positive descriptive window) all pass.

## Interpretation

For these retained measurements, the measured local useful-effect latency plus the retained subprocess receipt-drain maximum is small relative to the historical requested-route frontier-process gaps. Therefore **timing magnitude alone is not a reason to reject a bounded inference-gap composition experiment**.

This is not a causal end-to-end timing result. The source values come from different experiments. It does not show that local control remains useful for the entire frontier gap, that an XTEST/application effect tail fits the same allowance, that the requested model identity was actually served, or that task speed/correctness/tokens improve. Live composition remains owned by the narrower T2/X11 successors.

The exact generated `RESULT.json` is retained deterministically as `RESULT.json.gz.b64` using `gzip -n` then base64. Decode+gunzip reproduces raw SHA-256 `4d75ef5b02776910f7fb293c50d975f36acfc05c3155f57b5549046dc1fc6ed8`.

`AUDIT.json` SHA-256: `100846c410132f8c22b43a00e657eeecfadc23452792b8b689070825abd3fbe7`.
