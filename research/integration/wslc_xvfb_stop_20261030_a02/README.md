# WSLc private Xvfb stopped-server successor A02

One predeclared exploratory successor to A01, with conditions and pass gates written before the run. WSLc 3.0.3.0, image ID and exact command in conditions.json, network none, read-only current-main runtime source, and a private Xvfb with dedicated output mount. The Docker source and loaded WSLc image have equal rootfs layers but different IDs and some config fields, as documented in A01.

All five tests passed. The retained receipt records cancellation completed while Xvfb remained stopped, old release not attempted, cleanup UNKNOWN, task success null and replay denied. After server resume, a separate client held A and A remained down after old close, which preserved the old release receipt. The test then released its own A hold, created a fresh target on the same X server, refused the old alias and observed one new B press with an independent synthetic-task oracle passing. Final readback reported A and B up, and the exact-ID cleanup query found no matching container. Eight checks in audit.json were calculated from retained files.

This is one synthetic schedule; fresh target admission here does not establish display-generation isolation. The old operation remains UNKNOWN. This does not establish WSLc general reliability, MAP01 completion, model/provider behavior, or comparative speed. The receipt is a test-produced record, not an independent external event stream.

`python independent_audit.py` independently recomputes 11 checks from the retained receipt and cleanup output, including event ordering, failed old terminal, stale-alias refusal, the fresh effect oracle and final key readback. All 11 passed. This re-evaluates the same test-produced evidence; it is not a separate recorder or an independent live run.
