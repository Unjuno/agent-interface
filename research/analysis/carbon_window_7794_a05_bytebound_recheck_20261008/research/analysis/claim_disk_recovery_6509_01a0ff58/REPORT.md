# Actual process-exit and disk-prefix construction result — #6509

Worker/session 01a0ff58-6178-7ea1-a6d5-cf09260b91e3; FINAL-v5.
Source base main: f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549.
Branch: research/claim-disk-recovery-6509-01a0ff58-20261003.
Result: PASS_PROCESS_EXIT_BOUNDARY_SCOPED.

## Why this boundary

Original #6509 T0 allocation-01 established a 45-row logical disposition model. Its report and independent comments explicitly qualify crash/replay/final-commit values as synthetic counters rather than observed disk/restart behavior. This additive package tests actual file/process behavior for a small receipt-prefix construction, while keeping authored verifier semantics. It does not adopt a new runtime mechanism.

## Executed result

One nine-case matrix ran once, with no candidate retry. Each writer wrote newline-terminated JSON receipts to its own new file, called flush and fsync, and exited abruptly through os._exit(73) at its assigned cut. Two subsequent child processes separately read the retained files. The parent captured all 27 exits: nine planned writer exits 73 and 18 reader exits 0. A separate auditor imports neither writer nor reconstructor; it compares retained journal bytes, exact authored case identities, source hashes, process outcomes and both recovery outputs against a literal nine-case oracle.

| Case | Actual retained cut/control | Reconstructed result | Current completed checks |
|---|---|---|---:|
| c01 | Exit after first flushed receipt | PARTIAL_UNKNOWN | 1 |
| c02 | Exit after second flushed receipt | PARTIAL_UNKNOWN | 2 |
| c03 | Exit after third flushed receipt | COMPLETE_VERDICT | 3 |
| c04 | Exit before cached-marker write | COMPLETE_VERDICT | 3 |
| c05 | Exit after cached-marker write | COMPLETE_VERDICT | 3 |
| c06 | Flushed, truncated third JSON record | PARTIAL_UNKNOWN | 2 |
| c07 | Flushed decisive identity-negative | COUNTEREXAMPLE | 1 |
| c08 | Current generation changed after publication | PARTIAL_UNKNOWN | 0 |
| c09 | Duplicate fourth receipt after publication | PARTIAL_UNKNOWN | 0 |

Counts: 3 complete, 1 counterexample, 5 unknown; 15 source-current completed-check records are available as descriptive reuse metadata across the seven admissible prefixes. This is not a measured reduction in executed verifier work: no semantic checks were re-executed on recovery.

The always-UNKNOWN comparator produces nine conservative unknown labels. The intentionally insufficient cached-marker comparator produces three complete labels; two are false complete labels for c08/c09. This comparator is a planted negative control, not the current runtime. Prefix reconstruction produces zero false complete labels on the frozen table. The two separate reads agree per case and each result carries the retained journal hash. No consumer operation or GUI/input authority is produced.

Six raw mutation controls were rejected: missing case, duplicate case, partial-to-complete promotion, stale-prefix reuse, writer-exit alteration and journal-hash alteration. Eight construction tests pass. Their initial unimplemented conservative stub produced four expected assertion failures; exact stub source is retained in tested-unimplemented-recovery.txt. Test-first logs are public redacted copies, with original/private hashes retained by the worker. First outcomes were not rewritten.

## What was actually measured and what remains unknown

Windows 11 Pro 10.0.26300, native CPython 3.12.14, C: filesystem, serial child processes, standard-library-only sources. The CPython executable hash and platform/version strings are frozen. Parent timeout: 15 s per child. Source and cases were frozen before the first nine-case invocation. Actual UTC start/end and commands are retained in RUN.json; exact private absolute invocations are retained by the worker. No timing comparison or statistical error estimate is inferred from these run boundaries. Disk filesystem type, physical storage model, OS write-cache configuration and power-loss behavior were not independently measured.

Check values, generation changes, scope and cuts are authored inputs; this does not measure real verifier truth or an application's effect. A flushed complete newline-delimited prefix was observed after planned process termination. This does not prove persistence under power loss, directory-entry durability, arbitrary write tearing, concurrent writers, transactional consumer publication, exactly-once external effects, malicious source authenticity, live deadlines, cross-platform transfer, GUI/input release, safety, performance or human tempo. A partial positive remains UNKNOWN. Only identity/effect false are decisive negatives in this declared model. A cached label grants no authority.

No backend/input, model, GPU, host clipboard, WSLc/container or shared runtime was used. The native environment was chosen because this is a Windows process/filesystem question; WSLc is absent from this worker's local environment. Children and outputs are confined to additive case directories; the only retained file mutations are authored fixture writes. No process remains running and no shared lease or main-writing lock was acquired.

## Evidence identity and delivery

FREEZE.json binds the six executable/test/case sources to this boundary ID; those sources were unchanged between freeze, candidate and audit. SHA256SUMS binds the public package, including all nine journals, three cached markers, raw, audit, logs and documentation. results files preserve their actual bytes through package-local Git attributes. Public test logs redact the private absolute package prefix; original bytes remain in the worker's local deliverables and private-provenance.json records both hashes.

This package is ordinary engineering construction and evidence only. Original #6509 T0/WSLc STOP/raw/source and dispositions are unchanged. Runtime code and hosted workflow definitions are unchanged. Publication through a PR is a delivery state, separate from this scoped result. FINAL-v5 nonauthor consensus, current-tree composition and conditional application remain necessary before main. Common fleet deadline has not been obtained; this package sets no new fleet deadline.

## Local validation limitations and publication repair

Package tests pass 8/8; analysis-index tests pass 17/17. The sparse analysis index check passes while preserving absent sibling entries; this does not claim a full materialized-tree index check. Public navigation passes 26 documents / 1,637 repository-relative links, and committed-tree workspace inventory reports 156 reachable top-level directories. Staged diff validation passes.

The existing workspace suite was executed on native Windows: 21 test methods, nine error reports, runner exit 1. Failed methods are test_current_default_fallback_without_git_is_preserved, test_document_symlink_rejected, test_hidden_regular_nested_unicode_and_tab, test_hidden_symlink_ignored, test_missing_root_and_git_error_fail, and test_symlink_entries_fail_closed (four subcases). Causes are Windows symlink privilege errors (WinError 1314), tab-containing filename rejection (WinError 123), and deletion of read-only temporary Git objects (WinError 5). These unchanged baseline tests are not asserted to pass. The original diagnostic output is retained privately; its redacted public copy and both hashes are retained in LOCAL_CHECKS.json. No elevation, shared configuration change or broad test repair was attempted.

The first publication helper exited 1 after its navigation/index/workspace-inventory/diff checks passed: the repository-wide *.log ignore caused git add to omit evidence logs, so staged-byte validation refused the missing audit.log. Subsequent publication helpers preserved the Windows workspace-test output but encountered CP932 stdout printing and default text-reading encoding errors. Those helper faults were corrected locally; captured outputs and passing checks were reused rather than rerun. Git diff then treated original CRLF log bytes as trailing whitespace; package-local attributes preserve logs as binary diff artifacts, without rewriting their bytes. The public failure log transcodes CP932 to UTF-8 and redacts private prefixes; original raw bytes remain private. The candidate/raw/audit were not rerun. Only this package's known log files were subsequently added explicitly with git add -f; root ignore rules remain unchanged. Original publication and recovered-test start/end were not separately collected. Hosted optional CI remains a separate delivery status.

## Versioned audit correction after independent review

Independent comment 5964379370 on PR #6891 found four copied-raw mutations that audit v1 accepts: a reader beginning before writer exit, child argv/mode disagreement, an unfrozen interpreter string, and a COMPLETE reason attached to a PARTIAL result. The original observations match that reviewer's independent checker. The defect is the automated gate's missing metadata/full-result joins. Original v1 checks must not be read as automatically validating UTC order, argv, frozen environment or every recovery field; those had depended on source/manual inspection.

Original audit.py, FREEZE.json, six source/case identities, all nine journals/markers, raw/RUN/audit/first logs remain byte-identical. Original documentation/manifest are copied under historical/ and identified by original head d6d27e98230f3dd0302a985dfab043126a4c1ff4. No writer/reader/producer or formal allocation is rerun. New audit_v2.py imports neither v1, writer nor reconstructor. It independently derives exact journal/marker bytes and every result field, and checks typed process schemas, literal child argv/case joins, frozen environment, and serial chronology bounded by original FREEZE/RUN. Recorded UTC is wall-clock metadata and is not independent proof of causality under clock adjustments or malicious forgery.

The pre-repair v2 delegate to unchanged v1 produced nine expected assertion failures across six test methods; source/log are retained. The four review controls and ten additional type/coverage/provenance controls now reject. Original retained data still yields 3 complete / 1 counterexample / 5 unknown, 15 completed checks and two false cached completions. FREEZE-v2.json is an ordinary post-discovery audit-source/input freeze, written after local repair tests and before the first standalone v2 raw audit; it is not an experimental pre-registration or replacement for the original source freeze. RUN-v2.json records actual audit/test UTC, argv, exits and output hashes. See AUDIT-v2.md. No stronger process, durability, semantic truth, external effect, authority or performance claim is added.
