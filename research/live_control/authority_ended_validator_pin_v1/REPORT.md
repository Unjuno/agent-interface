# Durable authority-ended validator source pin v2

Status: **RETAIN_SOURCE_PIN_CANDIDATE** in one frozen 15-case offline formal matrix. The earlier claimed-hash/callable candidate is retained as a pre-formal construction failure. No GUI/model/network/durable-submit execution and no production promotion.

## Trigger

The retained durable token state (`authority-ended-durable-token-state-v2`) stores only authority-end IDs, post sequences and pending/consumed state. Its implementation statically imports the original one-capture `authority_ended_bridge_v1`.

Cross-domain work needs a truthful two-capture validator. Merely replacing the validator in process memory is not a durable session contract: the token-state file does not identify the validator semantics that admitted its receipts.

## Baseline failure

The formal matrix first reproduces this gap. The same unmodified token-state file is opened under two different process-memory validators:

1. bridge-v2 semantics issue `baseline-v2` with post sequence 11;
2. the same file is reopened under bridge-v1 semantics;
3. bridge-v1 then issues the distinct `baseline-v1` epoch with post sequence 2.

Both entries persist under the unchanged `authority-ended-durable-token-state-v2` schema. This is not duplicate-authority corruption—the IDs are distinct—but it demonstrates that validator semantics can drift silently across restart.

## Rejected construction candidate

The first sidecar candidate stored `validator_id + caller-supplied validator_sha256`, while the caller supplied the callable independently.

A control used the correct bridge-v2 label and claimed bridge-v2 SHA while passing the bridge-v1 callable. The sidecar accepted the claims and the callable admitted a one-capture receipt. This design was rejected **before formal freeze**; no result ID was consumed. See `construction-failure-v1.json`.

## Source-pinned v2 candidate

`SourcePinnedValidatorLedger` takes:

- bounded `validator_id`;
- validator source path;
- bounded function name.

It reads and hashes the source bytes itself, dynamically loads the requested function from those exact bytes, and persists a separate sidecar:

```json
{
  "schema": "authority-ended-validator-source-pin-v2",
  "validator_id": "...",
  "validator_sha256": "actual internally computed source hash",
  "function_name": "to_caller_execution_decision"
}
```

The sidecar uses temp-file write, file fsync, atomic replace and parent-directory fsync. Existing token state without a sidecar is refused; there is no silent upgrade. A new session writes the sidecar before initializing the existing retained token-state implementation.

The token-state file itself is **not changed**: its top-level keys remain exactly `schema, entries`, and the schema remains `authority-ended-durable-token-state-v2`.

## Frozen formal allocation

Result ID: `authority-ended-validator-source-pin-v2-20260916-01`.
Formal retries: **0**.

Source SHA-256 frozen in GitHub before execution:

```text
189bd81dd884b7840b31ef01e453e62a6d850f5c14dbe925bce8fb4b016558d2  validator_source_pinned_ledger_v2.py
f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9  bridge_v2_semantic_snapshot.py
d317da77de5908c92d5cf9fbd49d3987355a04954f8dcd3db947d236380ee874  formal_runner_v2.py
72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4  retained durable_token_state_v2.py
2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e  retained authority_ended_bridge_v1.py
```

A manual dependency-hash typo in the first GitHub copy of the formal runner was detected and corrected **before** the formal preregistration and before result-ID execution. Git blob identity was checked against the frozen local runner before the formal allocation.

## First formal outcome

**15/15 PASS. Decision: `RETAIN_SOURCE_PIN_CANDIDATE`.**

The matrix establishes:

- unpinned validator drift is reproducible;
- source-pinned v2 admits the two-capture receipt;
- the separate sidecar contains the internally computed exact validator source hash and function name;
- token-state JSON shape/schema are unchanged;
- duplicate authority-end ID still rejects;
- matching validator source across restart recovers pending state;
- v2 -> v1 validator-ID downgrade rejects;
- same label with wrong source rejects;
- same source with wrong function rejects;
- consume then restart remains consumed;
- existing token state without a sidecar rejects;
- malformed sidecar rejects;
- a separate v1-pinned ledger admits a one-capture receipt;
- v1 -> v2 reopen rejects;
- a deliberate crash after sidecar persistence but before token-state initialization can be completed only with the same pinned validator source/function; a mismatched source rejects.

Independent retained-result audit: **PASS**. Formal result SHA-256: `00595ea65a308c76cac0e23d2da86b7b3e05d2dd19cb0df907fee6699071bd86`.

## Interpretation

The evidence supports validator **source identity as durable session metadata**, rather than relying on process-memory monkeypatching or caller-declared hash strings.

A sidecar allows this experiment to preserve the existing durable token-state schema while making validator changes explicit and fail-closed. It is not evidence that sidecars are the eventual production representation; a future schema version could inline the same contract more cleanly.

This result also clarifies the architectural split:

- runtime authority epoch identity: `interruption.intent_token`, exposed as `authority_end_id` only after a valid authority end;
- receipt semantics: versioned validator source/function identity;
- token liveness/replay: retained pending/consumed durable state;
- transport uncertainty: separate durable-submit journal.

Conflating these into one mutable caller object would weaken auditability.

## H / T / D / C / U

**H.** Validator semantics can be durably pinned across caller restart without modifying the existing token-state JSON by binding the session to internally hashed validator source bytes and function name in a fail-closed sidecar.

**T.** One frozen 15-case offline matrix over exact retained durable-token dependencies, one one-capture validator and one two-capture semantic validator. Zero formal retries.

**D.** **RETAIN_SOURCE_PIN_CANDIDATE** because baseline drift is reproduced, all candidate mismatch/corruption controls reject, matching v1/v2 sources admit their intended receipt forms, and the retained token-state JSON shape remains unchanged.

**C.** The sidecar creates a two-file initialization boundary. Sidecar-first makes a crash fail-closed, but recovery requires explicit `initialize=True` with the exact same source/function. A future single-file schema may be operationally simpler. Source pinning also assumes the local source file is trusted; it is not a malicious-code authentication mechanism.

**U.** Single writer, one local Linux filesystem, offline receipts only. No power-loss/storage-fault proof, no concurrent non-cooperating writer, no live GUI/model/network, no durable-submit composition. The bridge-v2 semantic snapshot is an interface contract for this experiment and does not repair or certify PR #168's unresolved formal executed-source provenance.

## Next smallest experiment

Do **not** consume a live Inkscape crash allocation yet. Two conditions must be met first:

1. PR #168 must repair or rerun its formal source provenance so the truthful live two-capture receipt is reconstructible from Git state.
2. The cross-domain receipt builder must combine the already-retained identity rule (`authority_end_id = interruption.intent_token`) with an explicitly pinned validator contract, without a test-harness monkeypatch.

Once both are true, the highest-information live test is one same-application Inkscape authority expiry followed by durable token issuance and the already-retained durable-submit precommit ordering, with one deliberate caller crash and separate-process read-only reconciliation. Motor/capture policy should remain fixed.
