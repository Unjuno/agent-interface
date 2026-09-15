# Inkscape authority-ended ABI-v2 → durable-token compatibility v1

Status: **RETAIN_COMPOSITION_GAP / HOLD_LIVE_CRASH_COMPOSITION**.

Upstream authority candidate: PR #168 head `d1c7d0531993b23a61c7f38e12d979c27948cf6e`.
Durable-token source: retained `DurableTokenLedger v2`.
Tracks #171.

This is an offline interface audit only. It does not repair or depend on the correctness of PR #168's claimed formal-run source hashes; it tests the current retained ABI-v2 shape against the existing durable-token contract.

## First outcome

Five of five frozen cases passed.

1. The unchanged `DurableTokenLedger v2` rejects the truthful current ABI-v2 two-capture receipt before token issuance because its imported bridge-v1 requires exactly one passive post-authority capture.
2. Replacing only the imported decision function in memory with the current bridge-v2 semantics permits the two-capture receipt through policy validation, then exposes the second incompatibility: `runtime authority_end_id required`.
3. Adding a **diagnostic synthetic** `authority_end_id` makes the unchanged durable token state machine issue one pending token at post sequence 11.
4. Reissuing the same diagnostic receipt is rejected as duplicate.
5. Reopening the durable state file in a fresh ledger recovers that pending token at sequence 11.

Decision: **`RETAIN_COMPOSITION_GAP`**.

The synthetic ID is a causal-control device only. It is not a production repair because the current PR #168 runtime/formal evidence does not emit a runtime-owned authority-end identity.

## Exact executed source identities

- `durable_token_state_v2.py` SHA-256: `72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4`.
- existing bridge-v1 SHA-256: `2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e`.
- current PR #168 bridge-v2 Git blob: `63639f44eba47a2842e57e3761730e6f6224e815`, SHA-256: `37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52`.

The tested receipt uses the current retained ABI-v2 values: `captures=2`, `sequences=[10,11]`, selected `sequence=11`, `selection_rule=latest`, zero post-release admissions, and the retained lifecycle timestamps.

## Separate upstream evidence-closure hold

While auditing this interface, two independent reproducibility defects were found in PR #168:

1. its timing summary labels `release_to_*` values using a different release/verification origin than the explicit terminal `release.verified_ns`, and one finished metric does not recompute from either obvious retained origin;
2. more seriously, the current bridge-v2 and normalizer-v2 bytes do **not** match the SHA-256 values claimed by PR #168's manifest/build script as frozen formal sources. The current exact Git-retained hashes are `37e54408…` and `dc664652…`, while the manifest claims `37e6551b…` and `dc98340c…`.

PR history confirms the formal evidence was committed at `38f40605` **before** the bridge-v2 (`9ca8fbbb`) and normalizer-v2 (`08e176fb`) source files were added. Therefore the claimed formal-run source bytes are not recoverable from that PR's Git history as currently retained.

This upstream issue is orthogonal to the compatibility result above, but it blocks live promotion. PR #168 should retain exact formal-run source bytes if recoverable, or rerun one fresh formal seed under source bytes committed before execution.

## Architectural consequence

Do not start the next durable-submit crash allocation yet. Two production-facing prerequisites remain after the truthful ABI-v2 representation is re-established under closed source provenance:

- the durable token layer must validate the accepted ABI-v2 policy rather than being statically coupled to bridge-v1's one-capture contract;
- the live authority-ending producer must emit a unique runtime-owned `authority_end_id` in the receipt that crosses into the durable token ledger.

The minimal implementation should not weaken duplicate protection or synthesize the ID in the caller. The identity must originate at the authority-ending runtime boundary and be retained with the terminal evidence.

## H / T / D / C / U

**H.** Direct current ABI-v2 → DurableTokenLedger-v2 composition fails first at bridge-v1 capture cardinality and then, once bridge-v2 policy is substituted, at the missing runtime-owned authority-end identity.

**T.** Five-case offline first-outcome matrix using exact retained durable-token/bridge-v1 bytes, exact current bridge-v2 bytes, and the current retained ABI-v2 receipt values. No durable-submit transport, GUI, model, or network.

**D.** **RETAIN_COMPOSITION_GAP.** Both expected interface failures occur, while a diagnostic synthetic ID proves the underlying pending/duplicate/restart state machine remains functional.

**C.** A separate token implementation might already decouple policy validation or a runtime path might emit an authority-end identity outside retained evidence. Repository search before freeze found neither.

**U.** The dominant uncertainty is upstream PR #168's formal source provenance. No live crash or exactly-once conclusion is claimed.

## Next smallest step

First repair/re-run PR #168 so current truthful ABI-v2 live evidence has closed source provenance. Then add one runtime-owned `authority_end_id` at the actual authority-ending event and version the durable token policy dependency to bridge-v2 (or inject a frozen validator explicitly). Re-run this five-case matrix without the synthetic control. Only after that passes should one same-application live crash-after-send/read-only-reconciliation experiment consume a real Inkscape authority-ended token through durable-submit.
