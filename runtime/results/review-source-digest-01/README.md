# CLI summary source identity — read-only integration

Built from commit `ac5461508e5266976e2a6800a160fe0035b2a6f8`.
The CLI summary retrieval recipe now carries the original report SHA-256;
`review --expected-report-sha256` checks it before loading referenced images.
Default review and MCP retrieval behavior remain unchanged.

The portable archive was invoked with Python `-I` from `/tmp`, outside the
checkout, against the retained save report from `cli-summary-primary-01/call-4`.
Original file, byte-identical copy and stdin returned exit 0 with the expected
source digest. Adding one whitespace byte to copied file or stdin returned
`invalid_receipt`, exit 2. The frozen original was unchanged. No input was
executed and no new GUI task was attempted.

Initial setup used the copied directory as the image root, while the report
contained absolute paths to original images; this failed with `image outside
run directory`. Its output is retained. The successful probe corrected only
the image root. This is not a runtime relaxation.

62 focused review/CLI/summary tests pass in the existing MCP venv. The initial
system-Python run had one missing-MCP-dependency error and was rerun in that
venv. The full local native check also passes; raw protocol/harness logs and
result JSON are retained. Source identity is relative to a supplied digest,
not producer authentication, task correctness, replay authority, model-visible
feedback acknowledgment or a speed/token/cost comparison.

`raw.tar.gz` includes the build, exact response bytes, original report/images,
changed copy, test logs and probe commands. Paths in retained reports are
historical absolute paths. `python -O verify.py` checks archive member identity
without extracting files; it does not interpret screenshots or prove perception.
