# Chromium V5 point-mint generation guard R01

## Question and frozen condition

When V5 mints a target handle from a model point, does it refuse if the target
process or window generation changed between the model's source observation
and the fresh observation used for minting, even when the pixel patch is
identical?

The harness calls the current `session_v33.Backend.execute` implementation
directly with a fake owner exposing the same retained source observation,
fresh observation, image, `TargetHandleStore`, and event sink. No X server,
browser, operating-system input, external model/provider, or user desktop is
used. The source and fresh observations keep focus, surface, geometry, and
pixels identical; each negative control changes exactly one 64-hex generation
identity. The positive control preserves both identities.

## Frozen outcomes

- Process generation changed: refuse before registry creation.
- Window generation changed: refuse before registry creation.
- Neither generation changed: mint one session alias backed by a private
  random registry ID; the receipt must retain exact source/fresh patch hashes.

Failure, exception, or changed fixture/source is retained and not retried under
the same run ID. The test has no authority to dispatch input.

## Implementation check

If baseline reproduces a defect, add the smallest source-generation equality
guard before `TargetHandleStore.mint`, rerun this exact contract in normal and
`-O` mode, and run the existing point-target and compiled-caller suites in both
modes. The fix is accepted only if both generation-change negatives refuse
without creating a handle and the same-generation positive still mints.
