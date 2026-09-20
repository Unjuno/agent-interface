# #3830 formal02 — local Docker synthetic mechanics

## Disposition

**PASS_SYNTHETIC_MECHANICS_SCOPED** for the standalone byte-delivery and
request-only recovery harness. This is not a test of the production CLI: the
harness does not import runtime code, and no backend, GUI, model, or provider was
invoked. The earlier formal01 `STOP_SETUP` in #3832 remains unchanged.

## H/T/D/C/U

- **H:** A normally returned short stdout write is rejected while its exact
  retained report remains available read-only; a request-only child exit stays
  unknown and non-replayable.
- **T:** One run in Docker Desktop Linux/amd64, using the pinned, already cached
  Python 3.12 image, `--pull=never`, `--network none`, read-only root, read-only
  harness mount, and a fresh output parent volume. A separate host process ran
  the auditor afterward.
- **D:** All frozen synthetic mechanics checks passed. See `formal02/` files and
  `MANIFEST.json` for raw artifacts, hashes, and exact runner details.
- **C:** No model/provider/API/GUI/native input/network/GPU, no installs, no
  prior artifact modification, one Docker formal invocation and no retries.
- **U:** This establishes only the synthetic helper's declared mechanics. It
  does not test the production CLI implementation, real pipes/transports,
  process/power-loss durability, task effects, or general reliability.

## Results

- Short-delivery writer returned 83 bytes for an 84-byte JSONL response. The
  delivered strict prefix still parses as JSON. The producer surfaced
  `INCOMPLETE_STDOUT_WRITE:83/84` rather than success.
- Retained report and recovered copy are byte-identical to the producer report;
  SHA-256 `5b2e5093bdbbe5224041956ab8d2e1a0085439220c48b8ddd293bf1f5df8e00b`.
- Completed synthetic dispatch count: 1. Request-only crash dispatch count: 0.
- Child exited 23 after request publication. Recovery returned
  `unknown_or_incomplete`, process state `unknown`, report missing, replay false.
- Complete-delivery control: 84/84 bytes and one dispatch.
- Independent host auditor: 16 checks, zero errors, scoped PASS.

The exact 83-byte delivered prefix is represented in the repository as
`formal02/short-write/delivered-prefix.base64.txt`; trim ASCII whitespace before
base64 decoding. A direct text-API upload of the binary-named file gained a
terminal newline on GitHub readback, so that non-identical blob was removed from
the PR branch tip. The decoded prefix SHA-256 is
`d0a398263d3044bcc40c658f258c448fc0ba70743eb24985a1ae97391fd21116`.

The data supports the stated synthetic contract only. Since the frozen formal
scope in #3833 asked for standalone mechanics and explicitly bounded production
claims, do not describe this as a production CLI regression result.
