# Win32 supervised standard-caller R25 — terminal result wait

R24's independent fixture showed the exact effect at 8.800 s and its persisted
runtime receipt showed verified release at 8.824 s, but R24's 8 s public wait
returned pending and the immediate close returned busy. R25 is a separate
one-shot experiment with a new fixture, target generation, session, program,
lease, and sentinel. It increases only the public result wait to 12 s.

The input-free preflight verifies the frozen main source and the exact R24 raw,
runtime report, and follow-up audit hashes. The live probe follows the same
public stdio-MCP observe/validate/dispatch path, retrieves the terminal report
before close, independently checks the fixture effect and event journal, and
records the actual release receipt timestamp. It uses no WSLc or Docker, and
has no retry, replay, cancellation, or fallback input path.

PASS requires one returned completed dispatch with verified all-up release,
exact independent effect/events, public close `closed`, clean owned-fixture
exit, and restored previous foreground. Runtime `task_success` remains null.
Any pending response or uncertain release stays `FAIL_OR_UNKNOWN`.
