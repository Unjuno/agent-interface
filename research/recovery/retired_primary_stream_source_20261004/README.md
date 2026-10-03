# Retired primary stream source and independent review custody

This is an archival rescue of closed, unmerged PR #6919 and two independent review packets, not adoption of its runtime patch or authorization to revive its retired sender. The author explicitly retired the old application route UNSENT in [comment 5967341263](https://github.com/Unjuno/agent-interface/pull/6919#issuecomment-5967341263). The fresh implementation owner is separate Draft PR #6979. Issue #57 remains unresolved.

## Exact preservation boundary

649 previously absent archive files are retained at their original paths: 51 input-error files, 204 stream-lifecycle files, 154 startup-ready files, 40 V2 review files, and 200 V3/composition review files. Each source Git mode and blob OID is preserved, including raw stderr, TAP, failed construction, failed audit, and private-path-to-public-derivative mapping records. Four new custody documents and one additive current integration navigation link are the only authored additions/changes.

The custody commit has ordered parents: current main, original #6919 tip fdef9c7243e80cfe02bb2659606d317d2142a9a3, V2 review tip 5dc492b5987afd4faf4e3c3b16ce60b785f8c645, and V3 review tip 9e919932ed5600f752d89fb7a48b137d71c8d727. The last review tip also contains the original #6919 history. Redundant explicit ancestry records each source identity; original intermediate versions remain available as history rather than flattened final files.

SOURCE_ENTRIES.tsv contains 1,066 original changed-path rows (413 + 40 + 613), covering 653 unique paths. The V3 review's source range includes the original 413 rows again; those are not 413 extra rescued files. Of the unique paths, 649 are exact archive images. The other four are historical-only variants of research/integration/README.md, runtime/host_v1/README.md, runtime/host_v1/primary_stdio.mjs, and runtime/host_v1/test_primary_stdio.mjs. Current runtime, tests, runtime README, and every workflow are kept byte-for-byte; current integration navigation is kept with one new qualified link. Old runtime variants remain recoverable from the parent histories but are not installed.

All three original refs are KEEP. No source/reviewer branch is retired by this rescue; the separate active #6979 route is neither merged nor closed by us. GitHub's observed PR state must be read after the archival merge rather than inferred from an ancestor-only “merged” display. Historical committee votes, application digests, sender receipts, and content labels are historical data, not transferable authority.

## Scientific and failure qualifications

- Original input-error evidence is source-frozen macOS Node 26.7 evidence, not fresh execution here. Baseline child exits and unhandled Interface errors, pending candidate outcomes, raw transcripts, and the first timing-dependency failure are retained. Finite method tests and author-only busy-guard compositions are not production or committee approval.
- V2 claims retain actual original native invocation records, first auditor failure (missing attempt enrichment), and the first flattened composition export's import failures. A later same-byte correctly laid-out export does not erase those failures. The independent 6178 reviewer held V2 content because the startup-ready ordering remained wrong; that reviewer did not independently reproduce the startup fault.
- V3 retains the first SyntaxError construction (both cases failed), the later correction of two originally overlooked stderr files and erroneous metadata claim, the unchanged V2 healthy/fault result 1/2, and fixed-source 2/2. The first directory-FD EISDIR induction instead produced EOF and is FAILED_INDUCTION, not a successful reproduction. Distinct write-only FD0 evidence is EBADF with ready before fault and CLI exit 2; the exact numeric F_GETFL flags were not retained and are not invented here.
- Startup hooks are controlled construction evidence, not real startup-device/TTY coverage. The independent V3 review retains five cases across V2/V3/isolated composition (15 worker fixture pairs), two V2 premature-ready violations and none in its V3/composed fixture. Its isolated 51/51 ordinary method result combines V3 + its UTF-8 source + the current relay, not the new #6979 implementation and not the busy guard.
- The V3 review's earlier unknown-disposition inquiry and later DISPOSITION_AT_PUBLICATION record coexist. Its first scope-fetch auto-maintenance timeout lacked full child streams; later activity is not recovery of missing streams. Source public derivatives preserve their documented private-prefix mapping, not reconstructed original private-file hashes.
- Saved-data semantic-corruption checks, reported native outcomes, platform versions and cleanups remain attributed to their original authors/reviewers. We only verify archival conservation. No archived producer, auditor, native probe, model call, container, or formal allocation is executed. No physical-task benefit, hard deadline, general byte bound, production qualification, or new current application vote is claimed.

## Navigation

- [Original input-error packet](../../integration/primary_input_error_57_20261003_01a0ff53/README.md)
- [Original stream-lifecycle packet](../../integration/primary_stream_lifecycle_57_20261003_01a0ff53/README.md)
- [Original startup-ready packet](../../integration/primary_startup_ready_57_20261003_01a0ff53/README.md)
- [Independent V2 review / CONTENT_HOLD](../../reviews/primary_stream_lifecycle_6919_6178_20261003/REPORT.md)
- [Independent V3 and isolated-composition review](../../integration/review_primary_startup_v3_57_20261003_45e9/README.md)

## Verification scope

Verification is a fresh full tree-mode/OID census against the candidate and, after merge, the actual first parent of the actual archival merge. Every preexisting main entry except the one intentionally extended navigation document must remain identical; all 649 selected archive images and all three original histories must be present. Source-ref and active-successor states are checked separately. New authored text is whitespace-checked separately from raw evidence; any raw-inclusive whitespace diagnostics are retained and reported, not normalized or silently counted as a passing global check. Runtime tests and archived programs are not run for this archival-only change.
