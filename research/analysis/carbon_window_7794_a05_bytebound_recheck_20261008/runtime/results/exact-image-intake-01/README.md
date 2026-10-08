# Exact-image reuse intake against retained primary Calc replies

Disposition: **RECONSTRUCTION_PASS / LIVE_ADAPTER_HOLD**.

The frozen A1r3 exact gate is a scoped research baseline: scripted real-app trials,
not model-token or end-to-end agent efficiency evidence. Its unchanged code and
three original construction tests were rechecked in WSL against three already
retained primary Calc streams. No new GUI, input, sensor, model call, or formal
research allocation was run. Each old stream begins with a fresh gate/receiver;
images and references are never reused across streams.

The 31 retained public replies contain 21 images. Four exact consecutive repeats
could omit their image bodies while reconstructing all 21 sampled frames exactly.
Their PNG bodies total 290,285 bytes out of 1,363,191 image bytes. All non-image
text is carried separately for every reply, including capture timestamps, target
identity and revision. Equal pixels do not imply equal target metadata, unchanged
application state between captures, redraw completion, or successful saving.
No hash/perceptual threshold decides equality: dimensions, mode and immutable
pixel bytes are compared, as in the original research. Hashes bind stored evidence.

Inputs are the immutable archives in calc-compact-primary-01,
public-review-live-01 and target-review-request-primary-01. result.json pins each
archive and every reply, and lists every image/reference decision. The independent
verifier decodes the original PNGs and derives consecutive equality without
importing the gate. It also checks context hashes and reference sequencing.

## Production boundary

Do not replace public MCP image blocks with references yet. The research receiver
assumes a reliable ordered stream with a retained full-image base. The current
primary-review recorder expects an actual delivered image in the same reply;
its ordinary public v2 receipt cannot currently attribute a referenced base.
Transport return, presentation callback completion and caller-declared review are
different boundaries, and none proves model ingestion. A new adapter must define
explicit base retention/acknowledgement, unknown-delivery handling, reconnect/reset
resynchronization, reference-aware review attribution, and full-image fallback.
Do not infer an acknowledged image base from a sent request or disk artifact.

This is image reconstruction evidence, not live interoperability. Actual model
input tokens/cost, extra reference metadata, compare/memory cost and end-to-end
latency are unmeasured. No default wait, capture, retention or model presentation
behavior changes. The 50/250 ms useful-feedback comparison in #3700 remains HOLD;
XDamage temporal-boundary results do not establish task or redraw completion.

Run python3 -O runtime/results/exact-image-intake-01/verify.py from this checkout.
It reads the three original archives without extraction or executing archived code.
