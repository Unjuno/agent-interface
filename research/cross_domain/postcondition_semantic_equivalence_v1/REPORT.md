# Semantic-equivalent JSON postcondition evidence

Task `POSTCONDITION-SEMANTIC-EQUIVALENCE-20260916-003`, Issue #423.

**Decision: `PASS_SEMANTIC_POSTCONDITION_SCOPED`.**

## Question

Completed Issue #410 showed that content bytes alone are insufficient when Git entry kind/mode are part of the requested after-state. This successor keeps ordinary blob kind, mode `100644`, changed-path scope, ancestry and current-OID CAS fixed and changes only the content predicate: exact serialized JSON bytes versus a strict authored parsed-JSON semantic predicate.

The requested semantic value is exactly:

```json
{"enabled": true, "threshold": 3, "targets": ["A", "B"]}
```

The task is explicitly representation-insensitive: key order and insignificant JSON whitespace do not matter. Extra keys, duplicate keys, invalid JSON, wrong values and wrong JSON types do matter.

## Frozen allocation

Publication BASE: `9558313ed704804031733031f9e9443ddffc54de`.
Pre-measurement freeze HEAD: `a81331770c9f0ff7a34ba54119e65db07fca5b7a`.

Exactly 72 first outcomes ran once: two policies × nine scenarios × four repetitions. No same-ID rerun, replacement, extension or post-result tuning occurred.

Policies:

- `exact_bytes`: canonical serialized bytes must match exactly;
- `parsed_semantics`: parse JSON with duplicate-key rejection and require exact schema, JSON types and values.

Both policies also require candidate path `output/config.json`, ordinary blob type, mode `100644`, exact changed-path scope and final current-OID CAS.

## First result

| Policy | Ground-truth correct | False rejects | False accepts |
|---|---:|---:|---:|
| `exact_bytes` | 28/36 | 8 | 0 |
| `parsed_semantics` | 36/36 | 0 | 0 |

The eight exact-byte false rejects are exactly the two semantically equivalent representation controls (`equiv_key_order`, `equiv_whitespace`) × four repetitions. The semantic policy admits those 8/8 while still rejecting wrong value, wrong type, extra key, duplicate key and invalid JSON 4/4 each.

All eight `ref_race` cases (four per policy) pass content validation where applicable but the final Git current-OID CAS rejects publication after the target ref is externally changed. No race overwrites occurred. Candidate entry kind/mode/path and write scope remain fixed across all rows; unrelated state preservation and final refs/trees are independently audited.

Frozen independent audit: 72 rows, errors 0, `PASS_SEMANTIC_POSTCONDITION_SCOPED`.

## Construction and integrity

Before source freeze, the first excluded construction attempt exposed a harness-only Git tree-construction mistake: `git mktree` does not accept `output/config.json` as a slash-containing root entry. Only tree construction was repaired to create an `output` subtree and then the root tree. Hypothesis, semantic target, policies, scenarios, repetitions, CAS path and decision gates were unchanged. No formal row had run.

After repair, eight static semantic tests passed before formal measurement. The published source bundle is byte-preserving and was read back from GitHub before execution.

Frozen source SHA-256 identities and evidence hashes are in `FREEZE.json`, `SOURCE_BUNDLE.json.gz.b64` and `RESULT_COMPACT.json`.

## Interpretation

For this declared representation-insensitive JSON contract, exact byte equality is sound but unnecessarily strict: it rejects valid alternate serializations. A typed semantic postcondition can remove those false rejections without weakening the malformed-value or publication-race gates, provided the semantic predicate itself is explicitly authored and strict.

This does **not** imply semantic validation is preferable for every artifact. If byte representation, ordering, formatting, signatures, canonicalization or encoding are themselves part of the contract, byte-exact checking remains appropriate.

## Limits

The semantic predicate is curator-authored; no automatic intent, schema or dependency discovery is established. This is one local Git 2.47.3 JSON fixture with stageable immutable effects. No arbitrary application semantics, irreversible effect, GUI/model/network behavior, power-loss durability, performance, natural error rate or production integration claim follows.
