# Issue #5941 successor T0 — allocation-02

## Result

**PASS_METHOD_SCOPED** for this finite synthetic reconstruction and its mutation controls only. This is not evidence of improved production verifier accuracy or of runtime capture integrity.

The frozen deck has 66 ordered rows: 64 combinations of eight PASS/FAIL vote triples, four V2 exposure classes, and two commitment states, plus two explicit malformed-edge controls. Truth is independently assigned by verdict-triple index parity, rather than derived from the vote quorum.

The raw-only auditor reported `PASS`, an empty error list, and rejection of all six controls: dropped row, duplicate ID, falsified disposition, invalidated commitment, promoted exposed vote, and reordered rows. In particular, the exposure-promotion and commitment-invalidation corruptions changed a decision and were rejected, addressing the ineffective no-op control in allocation-01. The planted peer-exposed copied-vote witness is raw-quorum PASS but scoped `UNKNOWN_INDEPENDENCE`. Shared raw-observation exposure is not classified as peer-verdict exposure; unknown exposure and invalid commitments do not receive credit.

Descriptive counts over the saved deck: count-only false PASS = 10; exposure/commitment-scoped false PASS = 1; planted copied-vote case = 1. The remaining false scoped PASS (case `008`) has two valid, unexposed PASS votes against independently assigned FAIL truth. This is an explicit limitation: exposure filtering does not prevent independent or correlated verifier errors. These small, deliberately balanced synthetic counts are not estimates of real-world rates.

## Construction and execution record

Before the freeze, an initial construction test exposed a circularity: deriving truth from the vote majority produced no planted false-quorum witness. The generator was corrected before freeze to use an independent truth factor. The frozen construction suite then passed 4/4 tests, and `py_compile` passed. The scripts and their SHA-256 hashes are recorded in `FREEZE.json`.

After freeze, the candidate ran exactly once (`python runner.py`; exit 0), producing `raw-candidate.json` with SHA-256 `33fc6b9e651bf9880ea2a7abc978f6f15950798010ddf9cdaf6a9377f4dc4956`. The separate raw-only auditor ran exactly once (`python audit.py raw-candidate.json`; exit 0) and emitted `audit-result.json` with SHA-256 `bb1d792b7c6aed5dc11445bd9ddbf6df7335c2a0c3c4b06791887f15d58892e4`. No post-freeze candidate or auditor reruns were made.

Host CPU / Windows CPython standard library only. No Docker, GPU, model, GUI, network, or external input was used. Docker Desktop's `desktop-linux` context was visible, but its daemon API did not respond within a 10-second read-only probe; no shared allocation was started or altered.

## H / T / D / C / U

- **H:** A count-only 2-of-3 quorum can falsely PASS when V2 repeats a wrong V1 verdict after peer exposure. Discounting a valid peer-exposed vote should refuse that witness as `UNKNOWN_INDEPENDENCE`; shared raw observation remains eligible under this dynamic-edge rule.
- **T:** Enumerate the 66-row finite deck described above. Candidate emits raw and scoped decisions; independent auditor reconstructs outcomes and applies six corruption controls.
- **D:** Pass method-scoped only when all 66 rows reconcile; the copied-vote witness changes from raw PASS to scoped UNKNOWN; shared-raw exposure remains eligible; unknown/invalid evidence gets no credit; independent audit has no errors; and all six controls are effective and rejected.
- **C:** The model assumes correctly captured exposure and commitment fields. Static failure-domain filters, independently captured call-boundary commitments, or non-voting cross-review may provide alternatives. Two independent/correlated errors can still yield a false scoped quorum.
- **U:** Synthetic finite model only. No LLM conformity, runtime integration, call-boundary attestation, GUI/task effect, performance, human, or production claim.

## Reproduction and integrity

Run `python -m unittest -v` for the construction suite and `python audit.py raw-candidate.json` for the frozen raw artifact audit. These commands verify the retained artifacts; they are not a rerun of the candidate experiment. `PROCESS.json` records invocation limits and artifact digests. `SHA256SUMS` covers the retained package files other than itself.
