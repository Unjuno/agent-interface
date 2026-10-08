# Supplemental replay receipt: recovery review, 2026-09-30

## Disposition

**RETAIN_SUPPLEMENTAL_RECEIPT_ONLY.** The two original PR #5039 files are preserved byte-for-byte. This review independently verifies the current availability and identity of the referenced report and three source files. It does not independently verify the historical Docker invocation or repeat the reported replay/audit.

This is additive evidence preservation, not a new formal allocation, a replacement result, or acceptance of [Issue #3311](https://github.com/Unjuno/agent-interface/issues/3311). The original `PASS_REPLAY_BYTE_IDENTITY` remains the historical receipt's disposition, with the evidence limitations below.

## Pinned provenance and static checks

- Source PR: [#5039](https://github.com/Unjuno/agent-interface/pull/5039), head `76966f916fb513d1eb43ccce7e2ada0db669ef4c`
- Recovery intake main: `30d98dcf65e9d5a1772083b416b84753f28f0b4e`
- Historical source main named in the receipt: `d5a8efa79b6f8462c8ce97fc19ca4ddd5875fe68`
- Method: read-only GitHub retrieval, exact byte hashing, and static JSON inspection. No repository source, probe, auditor, model, GUI, container, or workflow was executed for this review

The following complete retrieved contents recreate their advertised Git blob IDs:

| Retained object | Git blob | SHA-256 |
| --- | --- | --- |
| `reaudit/AUDIT.json` | `f67a85b010c3ca8bdbe5bbf918b95aae37e48c4b` | `78cc5b65959a1555964396853ea921f9778a88f4a1f64e70d5e500320f5f9f64` |
| `reaudit/README.md` | `655d5e71960fa60812864945c754a6b5dd34f81d` | `c055bb4c27c92979484e2c1875cd84795f76ae4b377502ecdce8fd0f004a7f83` |
| Existing replay `README.md` | `bdde8c59b16d7feb893ddf36e128945260ac448a` | `fe890074de9d92f0c4cbfd36b97d64aa80850226d5f0e0a860e5bf81947aef0f` |
| Existing `results/supplemental_docker_replay_01/REPORT.json` | `a674b924350bf8ff05e41f1007d2df4be1700fab` | `abef335e3949476510e083b5692e95edec5c971818c44ae9232d943fd315db36` |
| `research/live_control/compiled_gui_interface_v1.py` | `0c02db714127c8e0f770f9d4ac03699749899d2b` | `93e47e1ab5ae3450bb4acf9ec9d21c9abc44ca93ffaee25683b22039d9a722ca` |
| `research/live_control/probe_compiled_gui_interface_v1.py` | `ad43121baf654f0279447833a4d2ec90b16ecbe2` | `963e932dfeb3a94521d600c867319d96ad40883d7ed7c1ad14e9050f4304f18d` |
| `research/live_control/adaptive_acquisition_caller_v1.py` | `9c2200699243822fb11947ca3b4050433ada4b9f` | `cba8667e316bbd09403ef01f5c0b4b26a891ef3d8612ff63efa90276dfc6d37d` |

The report is exactly 75,579 bytes. Parsing its retained JSON finds 15 scenario entries and four invalid-control entries, each recorded as `true`. Its three `sources` hashes equal the retrieved source bytes and the audit receipt's declared source hashes. Those three source Git blobs are unchanged between the historical source ref and recovery intake main. These are current byte-identity and recorded-count checks, not newly observed scenario outcomes.

## Historical claims and missing process evidence

The original receipt reports one successful Docker replay, an independent second-container byte audit, and three pre-scenario output-mount setup STOPs. The two-file PR delta contains summaries only. It does not contain the independent auditor program, its exact command, a separate replay-output copy, raw process stdout/stderr/exit receipts, Docker inspection evidence, or separate logs for the three setup STOPs. Those execution claims remain author-reported historical claims; the present static verification does not independently establish them.

The already-main replay README names image `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; the subsequent reaudit receipt names `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Preserve these as distinct replay records. Matching report bytes do not establish identical execution environments.

## H / T / D / C / U

- **H:** The original supplemental receipt can be preserved with exact, reachable report/source references and without expanding its scientific claim
- **T:** Read the pinned PR delta and referenced files; independently recompute their Git blob identities and SHA-256 values; inspect report counts and hash bindings without executing the study
- **D:** RETAIN_SUPPLEMENTAL_RECEIPT_ONLY: current referenced bytes and recorded counts reconcile. Historical process authenticity and a separately reproducible independent-auditor execution are not established by the published delta
- **C:** A summary receipt can agree with an existing report while omitting the process evidence needed to establish a separately executed replay/audit. Hash agreement does not exclude that explanation
- **U:** No live X11/Chromium task, model/provider use, token or latency saving, amortization, portability, runtime adoption, product acceptance, or #3311 cold/warm/invalidation/repair benefit is established. The existing setup STOPs and all prior scientific dispositions remain unchanged

Integration review and CI apply separately to the final PR head. This note does not certify an unobserved future merge or its checks.
