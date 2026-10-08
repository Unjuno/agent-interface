# Archival qualification: W2 lease-to-actuation binding host evidence

This additive archive preserves the exact 36 published files from [PR #5119](https://github.com/Unjuno/agent-interface/pull/5119), head [`4d2d0b055df52c7f289712c54c632b6e20ce04be`](https://github.com/Unjuno/agent-interface/commit/4d2d0b055df52c7f289712c54c632b6e20ce04be). The historical subtree is `13074cf72101bbe2325cd270c44136dd663ef1bc`. Original source, fixtures, freezes, reports, outputs and tests are unchanged. This qualification and the parent index entry are new commentary outside that historical 36-file set.

## Historical evidence and unchanged dispositions

- [RESULT_v3.json](RESULT_v3.json) retains Windows host Python 3.12.10 construction results: v1 5/5, v2 6/6 and v3 4/4, totaling 15/15. This archive does not rerun or independently reproduce those tests.
- The four retained [v3 CLI runs](cli_v3/) each contain eight cases and record 14 reconstructed decision rows (11 input-edge rows plus three `NO_INPUT_EDGE` rows). Their raw audits retain `PASS_BINDING_RAW_AUDIT_SCOPED` and empty error lists. Separately versioned matched controls retain four matched target cases; the foreign target retains two rejection rows and the missing target two HOLD rows. The historical report records a candidate-disposition tamper rejection. These are finite host-construction records, not a general completeness or security certification.
- [host_cli/REPORT.md](host_cli/REPORT.md) and [host_cli/RESULT.json](host_cli/RESULT.json) preserve the older full-CLI counterexample. Starting from the original fixture, the target lease-open actuation changes from absent to `FOREIGN-ACTUATION`; both the frozen verifier and separate raw auditor are recorded as exiting 0. The verifier retains `COMPLETED_RELEASE_BEFORE_TERMINAL`, `unauthorized=false`, and 298 ns guaranteed / 302 ns possible occupancy. This is a synthetic old-checker boundary, not a live-input or runtime finding. The digest discrepancy below qualifies one retained metadata binding without rewriting the evidence.
- The original fixture still lacks lease-open actuation bindings for `release-before-terminal` (A4), `overlapping-key-holds` (A5), `missing-and-out-of-order-edge` (A6), and `held-input-no-effect` (A8). These original binding cases remain HOLD. Versioned positives do not confer authorization on the unchanged originals or rewrite their prior results.
- The v2 scalar rule binds one lease-open actuation to that actuation only. Its retained A4/A5 control is scoped construction evidence and does not select broader protocol semantics.

## Published-byte verification and metadata discrepancy

This archival inspection used repository reads, static source inspection, JSON parsing, byte counts, Git-object hashing and SHA-256 calculations only. No retained Python module, test, candidate, auditor or replay script was imported or executed. No new counterexample was run.

All 36 materialized paths match the pinned Git blob SHA-1, mode and byte length. The 36 paths contain 35 unique blobs because the baseline effective trace and fixture share the same exact blob. The 18 v3 source/fixture/output declarations (six in `FREEZE_v3.json`, twelve in `RESULT_v3.json`) match the retained bytes. An expanded check of 31 declared source/fixture/output hash references across v1, v2, v3 and the host-CLI result found 30 matches and one mismatch:

- `host_cli/RESULT.json`, `runs.baseline_auditor.output_sha256`, records `4349c0ab450899c2ab37882ee40f106122b2c95e7deed2bc79b6990f4eb210cd4`
- The exact published `host_cli/baseline.audit.json` has SHA-256 `4349c0ab450899c2ab37882ee40f106122b2c95e7dee2bc79b6990f4eb210cd4` and Git blob `672b9d5359b08761021ccd6c2867a6f17da83682`
- The recorded value has 65 hexadecimal characters and is not a valid 64-character SHA-256 representation. That historical field remains untouched. It does not bind the published output exactly; archival readback cannot establish which bytes were present during the original invocation

Matching published hashes establish archival identity and internal bindings where checked, not execution provenance, temporal validity, or the correctness of the historical test/audit conclusions.

## Source-derived denominator limitation; not executed

At the pinned head, [`audit_binding_gate.py` lines 33–52](https://github.com/Unjuno/agent-interface/blob/4d2d0b055df52c7f289712c54c632b6e20ce04be/research/orchestration/o2_g1/w2_lease_actuation_binding_5101_v1/audit_binding_gate.py#L33-L52) compares the case-ID sequence supplied by the raw trace with the case-ID sequence supplied by the candidate report and reconstructs only their paired rows. It does not enforce an independently frozen eight-case denominator or fixed case-ID set. Lines 28–31 check the candidate schema and agreement with the supplied trace's digest, rather than binding that digest to an external expected corpus.

Static consequence: with the expected candidate schema, a matching digest for the supplied trace and matching empty case lists, neither identity comparison nor the reconstruction loop necessarily adds an error, and line 52 can select `PASS_BINDING_RAW_AUDIT_SCOPED`. This is a source-derived limitation, not an executed counterexample. No empty-input artifact, new raw output or experimental result was generated. The four historical retained runs do each contain eight cases; this finding does not change their recorded dispositions or claim that they were empty. It limits what the auditor alone proves about omission or corpus completeness. Any repair or new corruption experiment belongs in a separately frozen successor, never an in-place alteration of this archive.

## Draft, resource and successor boundaries

At archival inspection on 2026-10-01, PR #5119 remains open/draft at the exact head above and [Issue #5116](https://github.com/Unjuno/agent-interface/issues/5116) remains OPEN. The [latest owner navigation checkpoint](https://github.com/Unjuno/agent-interface/issues/5116#issuecomment-5922926580) retains the original HOLDs, requires fresh source/image/output freeze and explicit resource assignment for formal work, and grants no allocation. The [v3 owner record](https://github.com/Unjuno/agent-interface/issues/5116#issuecomment-5861290400) also retains the draft/formal gate. The [resource request](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5861024359) was request-only; later queue arbitration repeatedly names other lanes and does not transfer their allocations to this package. No named transfer to #5116/#5119 was found in the inspected owner/queue comments. Archive publication does not clear the source PR's draft or merge/formal holds.

The later close-order diagnostic and finite open/close policy are distinct work under [Issue #5127](https://github.com/Unjuno/agent-interface/issues/5127), including merged [PR #5129](https://github.com/Unjuno/agent-interface/pull/5129) and [PR #5148](https://github.com/Unjuno/agent-interface/pull/5148). Their merged status does not upgrade #5119, erase the old-checker counterexample, close #5116, or resolve this auditor's denominator boundary. Consult that successor before duplicating close-order work.

This archive supplies no Docker/formal validation, live-input evidence, timing proof, owner/session proof, runtime-authority proof, GUI/model/task-effect evidence, resource allocation or issue closure. No container, model, live runtime, experimental execution or new allocation was used for this archival work. Any future formal attempt still requires its own fresh freeze and explicit ownership gates.

## Preservation contract

- Preserve all original 36 paths, bytes, modes and Git blob IDs, including the malformed recorded digest
- Do not normalize or repair freezes, reports, fixtures, historical result labels or the frozen auditor in place
- Keep new commentary separate and read the original README/results with this qualification
- Treat the archival base as a publication snapshot only, never as a refreshed experimental freeze
- Recheck main, destination-path collisions, index changes and latest owner restrictions before any separately authorized publication; retain #5119 draft and #5116 OPEN

