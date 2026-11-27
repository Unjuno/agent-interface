# Current-main Windows recheck — standard caller / Fake X relay

This packet records local test execution against main
`168200eb43dd0f9144b3ed4aef551387674c7bfd` on Windows 10 build 26300 with
Python 3.11.9. It rechecks the current standard owned-process caller, the
offline X11 reply parser and the FakeSocketRelay composition. Exact package
versions and commands are in [conditions.json](conditions.json); raw normal and
optimized output is retained under [raw](raw/), with hashes in
[SHA256SUMS](SHA256SUMS).

The owner/cancellation/XRes-fence group passed 39/39 tests in normal mode and
39/39 under `-O`. The parser/relay/caller group passed 29/29 in normal mode and
29/29 under `-O`. The groups intentionally overlap on the standard-caller
composition test.

The first run in this sparse checkout could not import the omitted relay files;
the next run also found the corresponding test modules omitted. Those were
checkout omissions, not test failures: the exact tracked source and test files
were materialized unchanged, after which all four runs passed. The retained raw
files contain the successful complete runs.

This is Fake X/socketpair construction evidence only. Existing tests keep
release `UNKNOWN` when disconnect or release is uncertain and keep the late
queued-DOWN counterexample from becoming a success claim. These results do not
show real X-server queue ordering, operating-system key-up, a physical release
deadline, independent product-application task success, or MAP01. No WSLc,
Xvfb, desktop input, or experiment allocation was used. The result does not
replace the still-required server-side ordering evidence.
