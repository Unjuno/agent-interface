# Canonical receipt pointer repair — #6873

Both legacy receipt decoders accepted noncanonical JSON Pointer array positions:
negative/positive-signed indices, leading zeros, whitespace, Unicode digits and
underscores. Python `int()` traversal resolves these to an existing array slot;
the declared pointer format does not permit them. Twenty unchanged-source probes
accepted invalid pointers. The existing native multi-reference decoder already
rejected them.

The repair reuses that strict walker for event receipts and single-observation
native receipts, preserving their existing root/marker restrictions. Invalid
escapes and unresolved positions also raise ValueError. Valid numeric-looking
object names, `~0`/`~1` escapes, canonical arrays and explicit `/report` references
still reconstruct correctly. Input objects remain unchanged.

Validation on Windows/CPython 3.11.9:

- Regression before repair: 7 test methods, 24 failing subtests and 2 IndexError
  errors. After repair: all 7 methods pass.
- Independently audited finite corpus: 1,111 tokens across 3 decoder formats,
  3,333 rows, 6 valid expansions and zero mismatches/input mutations. Five
  copied-output corruption controls are rejected.
- Related receipt/review/public presentation tests: 39 pass with isolated
  `mcp==1.30.0`. First attempt without optional MCP: 32 tests, one import error,
  preserved. Transitive package versions are in ENVIRONMENT.json.
- A portable zipapp built from the committed repaired source retains its exact source digest; nine isolated archive smoke checks pass. See ARCHIVE_CHECK.json.
- Existing Runtime unified CLI workflow test entry: 128 tests, 122 pass and six
  Linux-only skips. Compile entry and machine-readable doctor both exit zero.
  The skips are the Linux pipe transport test, four Linux exclusive-publication
  tests and actual Linux/X11 backend selection. No skipped test is counted PASS.

The new regression class is imported by existing `test_receipt.py`, so the
existing CI entry includes it without editing a workflow. Original baseline
source bytes, probe outcomes, raw finite results, independent audit, command/exit
receipts and lossless diagnostic logs are retained. SHA256SUMS covers the package;
validation-logs.zip was read back against each retained diagnostic digest.
The initial CRLF diff-check failure and setup errors are construction notes;
they are not scientific outcomes. No formal allocation was consumed or retried.

Reproduce from the repository root with fresh output filenames:

```powershell
python -B -m unittest -v runtime.cli_v1.test_receipt
python -B runtime/results/receipt-pointer-01a0ff59/boundary.py work/receipt-pointer-raw-new.json
python -B runtime/results/receipt-pointer-01a0ff59/audit_boundary.py work/receipt-pointer-raw-new.json runtime/results/receipt-pointer-01a0ff59/FREEZE.json work/receipt-pointer-audit-new.json
```

These are finite engineering checks of parsed JSON presentation, not benchmarks
or formal/runtime acceptance. Python 3.12+, other operating systems, arbitrary
JSON schemas/duplicate keys, live backend behavior, task effects, safety rates
and latency were not established by this host check. The current compactors
already produce canonical paths; no normal producer corruption is asserted.
No GUI, input, model, container/WSLc, GPU or shared resource was invoked.
No main application occurred; FINAL-v5 non-author review and conditional apply
remain separate. See PROTOCOL.md, FREEZE.json and Issue #6873.

Specification: [RFC 6901, evaluation](https://www.rfc-editor.org/rfc/rfc6901.html#section-4).
