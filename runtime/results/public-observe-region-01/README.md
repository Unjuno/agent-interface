# Public observation region authoring integration

Code: `8e4af9ccd7c012689ff3b15a8b7fa57749e13dd2`.
Portable runtime SHA256:
`c0cce99c32a1a1dd0fe234ced8e3e56f610ccff8d8ea56d62301407fcc0e6881`.

During the primary Operations World smoke retained in
[private-x11-readiness-01](../../../research/live_control/results/private-x11-readiness-01/README.md),
the assistant used the standalone observation tool's `region` array inside a
public dispatch program. This was refused before input. The embedded example
already documented x/y/w/h, but the differing forms still caused a real extra
request and correction. The original failed request and reply remain frozen.

The public API now accepts the same explicit `[x,y,width,height]` array for an
`observe` operation and lowers it to the existing core coordinates. Legacy fields
remain valid. Mixed forms, region on another operation, wrong-length arrays,
booleans/floats and invalid bounds refuse before dispatch. No coordinate guessing,
coercion, input retry, additional wait or authority issuance is introduced.
Static validation and dispatch share the lowering function. Text-gap and key-repeat
expansion occurs afterward, preserving source-index mapping. Core validation is
unchanged and still requires x/y/w/h.

## Validation and real use

- 267 protocol + 118 harness checks passed. Added controls cover malformed and
  ambiguous regions, no backend opening/no session dispatch on refusal, legacy
  form behavior, core/public distinction, original-program retention, and region
  lowering combined with both text-gap and key-repeat expansion.
- The first focused run failed one older assertion that expected region syntax
  to be invalid. Its log is preserved; that assertion now tests a genuinely
  missing x coordinate, and a new accepted-region case checks refusal diagnostics
  do not falsely label a statically valid program invalid.
- A fresh primary-operated allocation, `ops-world-primary-03`, used the built
  runtime through public persistent-X11 MCP. Same known debug seed 42/family 99173
  and real-time game configuration as the prior smoke; alerts/watchers disabled.
  Source and seed are known. No hidden evaluation or helper model was used.
- The six actual calls were observe, region-form forward/observe, deliberately
  mixed-form negative control, region-form camera/observe, Alt+F4, and close.
  Forward and camera programs completed with their original operation counts,
  640x360 images and verified empty releases. The mixed-form negative control
  contained an earlier key chord but returned `input_dispatched=false` for the
  entire program. Game and relay exited normally with code 0; owned processes
  were reaped. Evaluator report was read after exit and records success **false**.

## Limits

This demonstrates removal of the observed syntax rejection and preserves the
malformed-request refusal boundary. It is not a controlled comparison of model
authoring success, useful-feedback latency, game skill, human tempo or token cost.
The new normalization receipt retains the original program and therefore adds
response metadata when the new form is used; no token reduction is claimed.
Image review notes bind to exact reply hashes but are caller attribution, not
independent proof of understanding. Public caller-asserted source/lease rules
and fixed-delay semantics remain unchanged. Game tasks were not completed.

`raw.tar.gz` retains 70 files: requests, replies, images, reviews, reports, source,
runtime archive/build identity, fixture script, tests and prior refusal. No raw
file is overwritten. The verifier checks integrity, request/normalization/image
binding, completed operations, refusal, cleanup and scoped outcomes without
extracting or executing those files:

```sh
python3 -O runtime/results/public-observe-region-01/verify.py
```
