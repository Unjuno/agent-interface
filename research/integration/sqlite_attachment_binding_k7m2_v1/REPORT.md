# #4360: attachment lifetime is not schema version

**PASS_ATTACHED_DATABASE_DEPENDENCY_BOUNDARY_SCOPED** from one prospectively registered 32-case allocation. The deliberately weak SCHEMA_ONLY comparator remains rejected. This is research evidence, not a production change or a SQLite/authorizer authorization defect.

## Question and integrated-path relevance

#4088 retains the preceding SQL-cache/read-receipt study. #4114 owns schema-reprepare replacement inside a single database and explicitly excludes attached databases. Neither is rerun, overwritten, or promoted here. This experiment tests a new lifetime boundary for #1713: a database alias on one persistent connection may name a different database while its numeric schema_version remains equal.

A reusable dependency receipt needs the source lifetime as well as the source-local version. The concrete integration decision is to refuse/rebuild prepared dependency evidence after a mediated source replacement, without globally refusing an unrelated alias change. This does not complete #1713, the desktop acceptance route, or ROADMAP.md.

## H / T / D / C / U

- **H:** Schema-only dependency reuse misses an alias replacement; per-alias generation binding preserves the scoped current dependency and rejects old prepared receipts.
- **T:** Eight fixed conditions, two policies, two repetitions, four immutable eight-case batches. Fresh private main/A/B/U files per case; real separate reader and peer processes; statement cache128. A and B are independently created with two tables and one view, naturally schema_version3; A.v_dep uses alpha and B.v_dep uses beta. No assignment to schema_version. Actual authorizer callbacks are recorded and always return SQLITE_OK. The peer mutates data through another connection and records independent snapshots. Preparation is one read transaction; validation and private effect publication share BEGIN IMMEDIATE. Full raw DB/SQL/IPC/exit bytes are retained.
- **D:** All32 cases,64 actor exits and4 batch exits must reconcile; frozen per-condition results, dependency/value invariants and eight effective semantic audit controls must hold. Source/infrastructure gaps are STOP/HOLD, not inferred scientific results.
- **C:** Complete cooperative mediation of ATTACH/DETACH, monotone per-alias generations, exact singleton queries, disciplined table revisions, one connection owner and no concurrent alias/schema replacement during validation are assumptions. Reattaching the same file may conservatively invalidate. No arbitrary SQL, UDF, virtual table, untracked owner, file-replacement or version-rollback guarantee.
- **U:** Finite directed conditions only; no natural error probability, performance/token benefit, GUI/model use, authentication, crash/power-loss durability, production adoption or general SQL completeness.

See the unchanged [PLAN.md](PLAN.md) for the exact table, variable/unit definitions and conditional proof. All counts and versions are dimensionless. Nanosecond RPC brackets are diagnostic same-container ordering evidence, not a calibrated latency estimate; no combined uncertainty or coverage factor is invented.

## First formal outcome

| Policy | Cases | Missing dependency | Extra dependency | Stale private effect | False refusal | Accepted | Refused |
|---|---:|---:|---:|---:|---:|---:|---:|
| SCHEMA_ONLY | 16 | 6 | 6 | 4 | 2 | 12 | 4 |
| BINDING_SCOPED | 16 | 0 | 0 | 0 | 0 | 10 | 6 |

For each of two repetitions:
- A-to-B replacement before preparation makes the weak cache retain alpha even though the actual query returns beta. Updating beta after preparation produces a stale private effect; updating obsolete alpha creates a false refusal.
- Replacement after preparation leaves the weak receipt validating equal local revision numbers on the wrong database and publishes a0 instead of B's current b0. The binding-scoped policy refuses with BINDING_CHANGED.
- Replacing only the other alias leaves slot's source intact; both policies accept. Stable relevant/unrelated data changes provide ordinary revision controls.

The candidate successfully refreshes metadata in the tested before-preparation replacement cases. It refuses changed current data and changed prepared source lifetimes. No refused case is counted as task completion or repair.

## Evidence, chronology and execution accounting

Intake and preformal main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`. Bounded MCP inspection covered README, CURRENT_GOAL, ROADMAP, recent open/closed Issues/PRs, a returned branch page and targeted searches. Unpushed work is unknown. The prior conversation's result was already registered under #4088, so it was not republished.

One excluded 16-case construction allocation completed with actual exit0; its case audit and eight controls passed. EXPLORATORY.json preserves the smaller initial setup check. There was no construction/formal timeout or source transport failure in this allocation. Construction outcomes informed the prospective fixed gates; this is not a blinded replication.

Eight readable source/plan/environment files were committed and their Git object IDs and lengths matched local bytes before any formal case. Public source freeze commit: `3a17157a8edff365a563a154b7571c67a12df48f`. FREEZE SHA256: `8b6b60ac113e64699654f5f1b3359426500dc370ad65442364d62c11570d6aaf`. Issue #4360 comment5832550467 records the commands and exact readback at formal0. It also clarifies PLAN's wording 'lexicographic declared scenario order': the explicit SCENARIOS tuple and nested scenario/repetition/policy loop, not alphabetic sorting. The source/schedule itself was not changed.

From the frozen local directory, `python -B supervise.py formal-01 0` through index3 each ran once, in the foreground, with25s child supervision and40s tool envelopes. All four actual child return codes were0; all64 reader/peer return codes were0. No rerun, replacement, pooling or post-freeze scientific edit. First result comment5832588858 precedes complete raw publication.

Unchanged audit.py imports neither actor.py nor study.py. In another process it reconstructs view/table dependencies, preparation and committed revisions, effect rows, requests/responses, order, SQL/callback evidence, exact file hashes and final read-only SQLite data. Result errors[]; audit SHA256 `a0eabe22a2ad9d673ad8ae0606a43b06b14cf1517ba1374b74401405964a6077`. Eight effective copied-record semantic controls all reject normally, including Boolean-as-integer repetition and missing exit. These test semantic logic with file-hash checks disabled, not a claim of full-archive adversarial soundness. Same author/separate implementation/process is not external human review.

## Raw publication and read-only reproduction

Nine binary segments and CAPSULE.json contain all651 original scientific/construction/source/metadata files,3,278,117 file bytes. The37156-byte XZ archive SHA256 is `b70eaa3def68636f697de0c692a46b3c9e78baea961f442773295ed668601f5a`; expanded tar SHA256 is `5a1607fd2145af1f1c1d8ccdf7b8c476e24d09f6ced11edd1c401e0a9e9cd194`. All nine uploaded Git blob IDs matched local objects. Checksums are integrity commitments, not authentication.

restore.py is a postformal, bounded data-only publication helper. It validates ordered part digests, compressed/expanded bounds and digests, regular safe unique member paths and complete counts before writing to an absent destination; it never imports archived experiment code. Tests include intact restoration and six rejection controls. Fresh extraction matched all original files and rerunning only the unchanged audit and controls gave byte-identical output. No scientific actor/DB allocation was rerun. Publication checks are local, not repository-wide CI or an external review.

```sh
python -B restore.py /tmp/issue4360-review
python -B /tmp/issue4360-review/audit.py /tmp/issue4360-review/formal-01 > /tmp/issue4360-audit.json
cmp /tmp/issue4360-review/AUDIT.json /tmp/issue4360-audit.json
python -B /tmp/issue4360-review/controls.py /tmp/issue4360-review/formal-01
python -B test_restore.py
```

Use fresh output destinations. Do not rerun the consumed formal allocation. The original absolute commands remain historical evidence and the auditor allows relocation by checking their role/source/basename identities.

Actual environment: supplied Linux x86_64 execution container, CPython3.13.5, SQLite3.46.1, kernel6.18.44, AMD EPYC9V74. CPU clock uncontrolled/unmeasured; Docker/gh/image attestation unavailable locally. No network operations in scientific code; network-namespace isolation was not attested. No model/provider, GUI, task input, credentials or user data. ENVIRONMENT.json retains the SQLite extension hash. Setup limitations are local, not a fleet-wide availability statement.

## Primary reference context

SQLite documents schema_version as a schema counter in the database header, not a global database identity. ATTACH establishes a connection-local database name. Authorizer callbacks are compile-time observations here. The study never modifies the schema counter or changes authorization decisions. This independently implemented weak cache is the tested object, not a supported production cache contract.

Primary sources: [schema_version](https://www.sqlite.org/pragma.html#pragma_schema_version), [ATTACH](https://www.sqlite.org/lang_attach.html), [authorizer](https://www.sqlite.org/c3ref/set_authorizer.html), [transactions](https://www.sqlite.org/lang_transaction.html).

## Remaining boundary

Known attachment generations are insufficient if an owner misses a binding change or query dependency. Keep unknown/unmediated sources unsupported, rather than relabelling them current. This research-only result permits inspection of the source-lifetime requirement, not silent shared-runtime promotion. Related domains are cache invalidation, database optimistic concurrency and resource-lifetime/namespace management.
