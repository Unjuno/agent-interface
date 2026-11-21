# Portable runtime distribution on main acbdfc0f9 — 2026-11-21

## Question

Does the portable zipapp still build deterministically from exact committed
source and start on the current Windows and Ubuntu WSL interpreters after the
recent main changes, without a checkout, download, permission grant, or input?

## Result

**PASS_DISTRIBUTION_AND_BASIC_STARTUP.** Built on exact main
`acbdfc0f9db00358cbb755baebe7c7641867aeda` with Windows CPython 3.13.14. The
archive is **786,369 bytes**, SHA-256
`11804313d731cbebe84d371ce6f3e23871a77a3bf8ccae569dedb68d6ea9e1ea`, and
contains 69 entries backed by 64 committed source files. A separate second
build was byte-identical. `audit_packet.py` verified the archive CRC, external
manifest, embedded `BUILD.json`, checksum file, all 64 source blobs against
the pinned Git commit, and reported zero mismatches.

The `runtime/distribution_v2` suite passed **21/21 normally and 21/21 under
`-O`** using a TEMP directory on C outside all Git worktrees. The first run
with TEMP inside the source worktree failed 3 tests: two nested Git fixture
setups returned errors, and a no-Git fixture found the parent worktree. That
failure is preserved in the `*-worktree-temp-failure.log` files. Running the
same tests unchanged with an external TEMP passed; no assertions or timeouts
were weakened.

From a separate directory outside the checkout, the archive's doctor and
`validate --help` exited 0 on both hosts:

- Windows CPython 3.13.14: promoted Win32 backend available; side-effect
  authority false.
- Ubuntu WSL CPython 3.12.3: promoted X11 backend available; side-effect
  authority false.

## Conditions and retained evidence

The package, builder output, external manifest, `sha256.txt`, conditions,
Windows normal/-O logs, initial TEMP-placement failures, second-build log,
outside-checkout doctor/help output and independent audit are retained beside
this report. `SHA256SUMS` covers the packet.

No package was downloaded. No model/provider call, GUI action, OS input,
permission change, Docker action, or WSLc allocation occurred. The tested
doctors only report backend availability and do not launch a target.

## Limits and next gate

This updates the package/startup evidence from the older `038486e1` pin to the
current main source. It proves deterministic packaging, validator/runtime
tests and basic CLI startup only. It does not establish live target
permission flow, a GUI task effect, cancellation/recovery reliability,
provider behavior, an integrated efficiency result, macOS startup or public
Research Preview acceptance. Issue #58 remains open; Issue #57 remains open.
