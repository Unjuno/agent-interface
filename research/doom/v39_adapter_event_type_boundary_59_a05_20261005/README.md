# V39 adapter event-type boundary — A05

## H / T / D / C / U

**H.** Rows carrying nested X-adapter edge evidence must not disappear from cardinality checks because their outer event is unrecognized or a legacy `input_release_transition`. Only a supported admission/DOWN and release-measurement/UP pair may expose adapter intervals.

**T.** Freeze A02B head `73ccfa7696c1b005be7c1c59e63d1c06dfe3674d` and the retained A01 raw edge pair. Run the five exact/conflicting duplicate cases, four unknown-event cases, and two legacy-transition cases against the frozen projector and candidate.

**D.** Baseline should falsely pair duplicate unknown DOWN/UP and legacy-transition UP cases. Candidate must pass all three targeted methods; unsupported/legacy cases must return incomplete receipts with null intervals.

**C.** See `A05_RESULT.json` and the separately run raw-derived `A05_AUDIT.json`; exact source/test/raw hashes and output are retained.

**U.** One retained synthetic fixture and deterministic projection only. No physical release, live X-server state, application consumption, task effect, threat response, bounded recovery, or MAP01 result is established.

WSLc uses the cached pinned Python 3.12 image, no network or image pull, one CPU and 512 MiB requested memory, read-only source/evidence and a distinct writable output, as UID/GID 1000. Host warnings are retained; memory/swap enforcement is not assumed.
