# JSON exponent overflow at the public relay boundary — #6869

FINAL-v5 worker `01a0ff58-ba92-7fd2-9317-d75b43383005`, 2026-10-03.
Ordinary engineering characterization and regression; no formal allocation.

## Result and repair

Baseline main `3116528f3abe0fec72cfc1b5b2b5b4b05538512e` rejects explicit
NaN/Infinity, but its default JSON float decoder turns `1e400` into infinity.
Four independently initialized overflow cases reached the inert client and
consumed request ID 1. The bounded 16-case characterization retains both exact
source variants: 32 rows total, four baseline nonfinite dispatches versus zero
candidate nonfinite dispatches. Both accept the nine authored finite/string/null
controls; the other three nonfinite controls already refused on baseline.

`mcp_relay.py` now checks finiteness in `parse_float`, before envelope validation,
request-ID consumption or SDK dispatch. Nested numeric tokens use the same hook.
Representable finite values, subnormals, signed zero, strings and existing
integer decoding stay unchanged. Python's existing integer-size and float
rounding/underflow behavior is outside this repair.

Executable repair commit: `458c00546a2e10e895d1d38e4bc58219284e6a8e`.
Before delivery, main `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549` was merged into
the dedicated branch. Its intervening changes were confined to analytical
archives/index entries; relay, packaging, dependencies and CLI check definitions
were unchanged. Source-byte checks and `SHA256SUMS` bind the retained variants.

## H/T/D/C/U

- H: float exponent overflow escapes a `parse_constant`-only nonfinite gate.
- T: four overflow controls; three explicit nonfinite constants; nine finite,
  integer, string or null controls; same-ID follow-up; existing no-replay tests;
  and a real SDK/stdio portable relay subprocess outside the checkout.
- D: refuse every authored nonfinite value before dispatch/ID consumption,
  preserve controls, and preserve ambiguous accepted-request/no-replay behavior.
- C: downstream validation may refuse malformed values, but does not establish
  a pre-dispatch refusal. The baseline portable relay returned rather than
  refusing the overflow request.
- U: bounded synthetic/API evidence only. No application effect, live input,
  GUI reliability, latency benefit, clock trust or general authority claim.

## Independent implementation audit

The raw-only auditor imports no relay implementation. It checks exact source
hashes, complete case/variant coverage, literal input, dispatch count, status,
ID consumption, same-ID follow-up and finite argument preservation.
`audit_v2.json` reconstructs all 32 rows and rejects eight authored corruptions.
This is an independently implemented oracle by the author, not a nonauthor
review or merge vote. Run it normally; optimized Python `-O` is unsupported
because its analytical checks use assertions.

Original auditor v1, its result and the reproduced `total_calls=true` equality
gap are retained. V2 adds strict integer checks and follow-up/request identity
checks; the original raw was not regenerated or rewritten.

## Local validation

- Windows CPython 3.12.14, MCP 1.30.0: the CLI workflow's nine test modules plus
  public relay tests: 127 discovered, 121 passed, six Linux-only skips.
- Separate public MCP server/clock tests: 27/27 passed.
- CLI workflow compile step and machine-readable doctor completed with exit 0.
- CPython 3.11.9 construction: final committed-source relay suite 6/6, including
  a real packaged SDK/stdio overflow refusal; supporting CLI run 115/121 passed,
  six platform skips. Python 3.11 is below the advertised portable support floor;
  the Python 3.12 result is the supported-version validation.

All failed checks remain: missing sparse selector setup; initial red test with
shared relay state; corrected isolated red cases; committed-baseline packaged
red case; a Python 3.13/global MCP 1.26.0 dependency mismatch; and missing sparse
legacy research source after the main merge. They were repaired as ordinary
construction/setup, not pooled or relabeled as formal results. The six final
skips are Linux pipe/exclusive-publication/X11 selection controls. Linux/macOS,
live backend and hosted CI results are unverified here.

## Reproduce

From the repository root with MCP 1.30.0 and Python 3.12+:

```sh
python -B -m unittest -v runtime.cli_v1.test_mcp_relay
python -B runtime/results/relay-finite-json-01a0ff58/probe.py > /unique/output/raw.json
python -B runtime/results/relay-finite-json-01a0ff58/audit_v2.py
```

The auditor reads this package's immutable `raw.json`. To audit a new probe,
copy the whole package to a distinct output directory and place its new raw
there; do not overwrite the retained evidence. Exact additional commands and
exit codes are in `EXECUTION.json`. Test-only absolute local paths in public
stdout are redacted; original logs remain in the author's private workspace,
with original/published hashes recorded in `PUBLIC_LOG_PROVENANCE.json`.

This package has no test-discovery entry point and no runtime import/build
registration. Probe/auditor programs run only when explicitly invoked.
PR/main delivery is separate from these scoped results; no main application or
FINAL-v5 approval is asserted by this package.
