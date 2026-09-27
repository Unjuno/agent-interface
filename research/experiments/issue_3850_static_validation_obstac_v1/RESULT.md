# Issue #3850 — Obstac static-validation detail, rung 1

Status: `PASS_SCOPED` for the preregistered four-row dispatch-facade contract allocation. This is not closure of Issue #3850 or an end-to-end recovery claim.

## H / T / D / C / U and outcome

- **H:** bounded static detail can follow an existing `INVALID_PROGRAM` refusal for the two observed malformed observe shapes without changing refusal, adding a dispatch, or emitting backend input; a valid-program refusal is not mislabeled and arbitrary unsupported op text is not echoed.
- **T:** four deterministic rows at fixed source/candidate: the observed `region` shape, observed `width/height` shape, a statically valid program with mocked backend `INVALID_PROGRAM`, and a 2,000-character unsupported op string. Each facade call used a mocked session, one dispatch and one close; no model, GUI, display, native input, capture, or network request.
- **D:** all four rows met the preregistered outcome. The two malformed shapes returned `refused / INVALID_PROGRAM`, `detail_source=program_validation`, and respectively `observe x must be int` / `observe w must be int`; both had recorded `backend_emissions=0`. The valid-program refusal had no `detail` or `detail_source`. The unsupported op returned only `unsupported operation` and did not echo `untrusted-`. All input objects were unchanged; dispatch and close counts were 1/1.
- **C:** source PR head `4d51fccac55433570bc714cfaf21c88531fe325d`; its runtime tree `7fae16c1766a36376d6c49f49a7fb0e68f93cb0d` and all 10 selected transitive blobs are recorded in `source_manifest.json`. Source base main was `51cc5f964bb36677ad6f9192ddd75d03ca7343c7`. OrbStack context, Linux/arm64, image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; network disabled, container root read-only, source/runner read-only, dedicated output mount writable. Runner checked the frozen commit/tree/image/freeze environment values and source blob/SHA256 closure. An independent auditor ran in a separate network-none, read-only container against read-only source and raw.
- **U:** proves only the deterministic public dispatch-facade response transformation under mocked refusal. It does not prove a native backend emitted no input; zero emissions are the mock refusal's recorded value. It does not test actual executable transport or user/model recovery calls/time, operation-index detail, product benefit, or general diagnostic accuracy. PR #3853's separate local/Docker CLI suites are distinct evidence.

## Formal result

One formal allocation, no retry. Raw contains four rows and has SHA-256 `615dde79e9b1e1f9eb891bbac9a8bd00939157b3edb8bfddd452899ae812c7ab`. Independent raw-only audit classified `PASS_SCOPED`, 4 rows, zero errors, and reproduced the raw SHA; audit JSON SHA-256 is `68e5569608cf6a809f8cc05d81131a96ba64e09571fe5b623fd95217d1b0694b`.

The audit checked the frozen source manifest, exact case set, row-level refusal/detail/emission/call-count invariants, and absence of the long caller string from the returned row. The retained row binds each case label to an input-program SHA256, but the raw record does not carry the input bytes; therefore the independent audit did not independently reconstruct/replay the input objects. This is an explicit audit limitation, not a broader validation claim.

## Construction history

- `construction-01/STOP.md`: no container started; host invocation had a mistyped image digest.
- `construction-final-02/STOP.md`: no row; runner path was passed as a direct executable instead of invoking Python.
- `construction-final-03/construction.json`: 4/4 mock rows under an earlier freeze; superseded for final freeze by the next construction.
- `construction-final-04/construction.json`: 4/4 mock rows under final freeze `15af12fe44fd33d269ce42a485cd0d6b6c9e94070a4dd633bca0cc543f0629a5`, SHA-256 `e8b2f2e4892125e2b1d1f8dedddeba10bb96be77ff6684003de77630eeaf261c`.

## Reproduction

See `commands.md`. The freeze and source manifest were committed before formal execution; the two setup STOPs and construction outputs were retained separately and not overwritten.
