H/T/D/C/U — MAP01 V39 event emit fault boundary A01

H: The current main event sink writes a release event synchronously to events.jsonl, then delivered.jsonl, then stdout, without an event-ID dedupe/transaction. An exception after an earlier append leaves a partial prefix in the observed files; blind retry duplicates the logical row in an earlier destination. ExecutorV13 instead marks release publication attempted before invoking emit and retains delivery_unknown without automatic retry.

T: Current main 6a2826d391b77496b69752609a6f07b6971b4b6f. Extract only the literal nested emit function from the pinned session_map01_v12.py Git blob e701035302da4802e0db463035c4d653a7e7618b. Inject one-shot exceptions at events open, delivered open, and stdout after both file appends. Record each destination's logical release-ID multiplicity before and after one synthetic retry. Include no-fault baseline. Candidate and raw-only auditor are separate WSLc runs with no network, one CPU, 512 MiB requested, read-only source. Executor source pins v12/v13 are inspected for the no-retry policy; they are not instantiated.

D: PASS_SCOPED requires exact SHA-256 source pins; AST extraction of exactly main's nested emit; baseline one row per sink; before-first fault yields 0/0 then 1/1 after retry; between-file fault yields 1/0 then 2/1; post-second-file/stdout fault yields 1/1 then 2/2; independent audit reconstructs every count and confirms stable logical ID. Any mismatch is FAIL_SCOPED. Provenance or execution setup failure before injections is STOP.

C: Injected Python exceptions test call boundaries, not process death, fsync/device failure, cross-file transaction or filesystem crash durability. A synthetic retry does not claim production code retries. ExecutorV13 policy is source-reviewed, not runtime-integrated here.

U: Offline deterministic source-bound sink contract probe only. No game, GUI, X11, OS input, application effect, recovery, useful feedback, threat response or Issue #59 completion. It does not repair or qualify the full #7805 owner/bridge/Executor composition.
