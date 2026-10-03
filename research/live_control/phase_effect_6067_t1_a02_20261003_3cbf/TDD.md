# Construction only

2026-10-03: test_qualification against a placeholder returning empty stable IDs,
zero boundary hits and zero unknown frames ran 5 tests with 5 FAIL (not import
errors). Literal expectations covered stable closed interval, both boundary
directions, nonoverlapping source, unknown nonzero pixels and boolean timestamp.
These are method tests, not scientific A02 observations.

Terminal formal-admission guard: 1 observed FAIL against a no-op, then PASS
after explicit STOP_READINESS_SOURCE_EXPOSURE rejection. This later delivery
guard is not the source that executed construction-01. It cannot promote failed
readiness into science. Full top-level package suite now22tests, including
subprocess checks of all three formal entrypoints refusing before output/native.
