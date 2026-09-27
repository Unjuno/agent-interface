# MAP01 schema-v6 endpoint preflight v1

This allocation asks one narrow question before any v33 live run: does the
actual Luna-low structured-output endpoint accept `map01_cover_policy_schema_v6`?
It supplies no image, launches no GUI and grants no input authority.

The allocation permits exactly one fresh endpoint request and zero retries. Its
private compatibility cache begins inside an output directory that must not
exist at verification time. The runner first checks every frozen source hash,
the absent output, the model/effort, and the one-request limit. A refusal,
timeout, runner exception or unexpected endpoint result remains in the output;
none may be silently retried or replaced.

Run the non-consuming freeze check from either Windows or WSL:

```text
python research/doom/run_map01_schema_v6_preflight_v1.py --verify-only
```

When model capacity permits, run the endpoint observation once from WSL:

```text
python3 research/doom/run_map01_schema_v6_preflight_v1.py
python3 research/doom/audit_map01_schema_v6_preflight_v1.py
```

`ENDPOINT_COMPATIBLE` establishes only schema compatibility for the exact
recorded CLI/model/request identity. It does not establish useful planning,
latency, gameplay, survival or task completion. An incompatible or failed result
holds live v33 work at this boundary while preserving evidence for a separately
versioned schema or environment change.
