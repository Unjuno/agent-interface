# MCP request and result retention integration

MCP now shares the CLI's JSON persistence helper: write an exclusive temporary
file, flush/fsync it, then replace the final file. A failed request save prevents
backend invocation. A failed report save preserves the actual execution outcome
in the immediate response, identifies the persistence error, and forbids replay.
An unfinished temporary report is never promoted by result lookup.

This bundle records local integration evidence for source commit
`6f66851eb5f453376e3262d3a5f449e89a2ed4a6`. It supports retaining the change for
review; it does not establish crash durability, server-restart recovery, or the
full desktop integration spine's completion.

## Evidence

- `focused-and-cost/tests-03-pass.log`: 34 MCP tests pass, including request
  persistence failure before dispatch and report replacement failure after
  dispatch. Failure injection uses mocks; no disk failure was induced.
- `focused-and-cost/tests-02-failure.log`: the earlier 34-test run failed because
  the new test report fixture omitted its schema. The fixture was corrected;
  the failed run is retained. `tests-01.log` is the earlier 33-test pass.
- `native/`: the local native integration runner passes 161 protocol and 68
  harness tests (229 total). Container `ai-mcp-retention-native-01` was inspected
  as exited with code 0. These are contract checks, not live desktop tasks.
- `live/`: the primary agent viewed the initial image, authored a program,
  validated it, dispatched once, and viewed `receipt-72` and `saved:receipt-72`.
  The primary completion declaration preceded reading the fixture's independent
  `effect.json`. Result lookup with the same call ID returned the same raw report,
  omitted the requested image, invoked no operation, and left all six retained
  request/report/image files unchanged. Input release was verified.

The live run used one persistent SDK-mediated public MCP stdio connection, a
private Docker Xvfb/Tk fixture, and no secondary model. It was not a registered
host tool call. Source/binding assertions were caller supplied (1/0); the owner
set a 10-second monotonic expiry immediately before dispatch. No disconnect was
injected. The isolated container exited 0; tracked Tk/Xvfb child return codes
were -15 and 0, respectively. That is not proof of general descendant cleanup.

`live/FREEZE.json` and `live/source/` retain the pre-run source closure;
`live/PLAN.json` retains the pre-run task and bounds. Absolute paths in original
receipts refer to the allocation, not this copied directory. The original
`live/check_result.py` is retained byte-for-byte and uses Windows separators;
use the cross-platform read-only verifier below to inspect this archive.

## Storage cost and limits

Six alternating pairs on this Docker Windows-mounted output path produced
median direct-write time **2.752205 ms** and shared-writer time **9.542832 ms**.
All 12 files had identical bytes. These timings are not a pure fsync comparison:
the direct path uses pre-serialized bytes, while the shared writer includes JSON
serialization. This small engineering check indicates added storage cost, not
a task latency estimate or a general performance distribution. The helper does
not fsync the containing directory. There is no model-input token measurement,
matched GUI baseline, human-speed claim, or six-domain/task coverage claim.

## Inspect without replay

From the repository root:

```sh
python runtime/results/mcp-retention-integration-01/verify.py
```

This checks archived bytes, frozen source hashes, recorded readback equality,
request counts, and application effect. It executes no GUI action and does not
rerun the owner or turn archived evidence into an independent adoption audit.
`MANIFEST.json` covers the copied original evidence, not this explanatory README
or verifier. The Dockerfile retains the local image composition; its base tags
refer to locally cached images, not published reproducible registry artifacts.
