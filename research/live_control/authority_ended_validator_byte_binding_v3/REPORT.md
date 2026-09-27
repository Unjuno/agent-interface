# Byte-bound durable authority validator v3

Status: **RETAIN_BYTE_BOUND_VALIDATOR_V3** in one frozen 17-case offline formal matrix. This supersedes the v2 source-path loader for any promotion beyond its trusted/non-mutating-source boundary. No live GUI/model/network/durable-submit execution.

## Trigger

The source-pinned v2 candidate computes SHA-256 from `Path.read_bytes()` and then asks `importlib` to execute the validator from the path. Those are two separate reads. Therefore the persisted hash can describe bytes A while the executed callable comes from bytes B if the source path changes between hash and load.

## Deterministic v2 counterexample

The formal matrix uses a controlled `Path.read_bytes` replacement hook:

1. validator source initially contains A, whose callable rejects;
2. v2 reads A and computes SHA-256 `573486797e1e8924cecf5e38c36744d7fcbc49c175b807e846d4b0a9a7105d63`;
3. immediately after that read returns, the hook replaces the path with B;
4. B's callable returns the safe-yield decision;
5. v2 persists A's hash but `importlib.exec_module()` reads B and the token **ISSUES**.

Final disk source B has SHA-256 `8d6762f8430be44b3b2adc1790356d07c65889fe61dcb0da5614ee744bc6e746` while the sidecar retains A's hash. This is a real hash-to-execution TOCTOU under the experiment's deterministic replacement model.

## v3 candidate

v3 performs a single source read and binds execution to those exact bytes:

```text
data = source.read_bytes()
sha = SHA256(data)
code = compile(data, filename, "exec")
exec(code, fresh_module_namespace)
validator = namespace[function_name]
```

The source path is never reopened to obtain validator code. Sidecar metadata still pins validator ID, exact byte hash and function name; the durable token-state JSON remains unchanged.

Under the **same** replacement hook, v3 stores A's hash and executes A's rejection even though the path has already become B. Thus source identity and executed validator bytes remain the same object.

## Formal allocation

Development had previously produced a local `...-01` result before formal preregistration. That ID was deliberately not reused. The frozen formal allocation is:

`authority-ended-validator-byte-binding-v3-20260916-02`

Formal retries: **0**.

Frozen source SHA-256:

```text
a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5  validator_byte_pinned_ledger_v3.py
f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9  bridge_v2_semantic_snapshot.py
91f1bb7f973b4bbb2c9967d8dbfaba82ccf272e6eedf13ebcf3e813fa7f140bb  formal_runner_v3_02.py
```

Pinned dependencies:

```text
189bd81dd884b7840b31ef01e453e62a6d850f5c14dbe925bce8fb4b016558d2  validator_source_pinned_ledger_v2.py
72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4  durable_token_state_v2.py
2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e  authority_ended_bridge_v1.py
```

Source Git blobs were checked against the frozen local bytes before formal execution.

## First formal outcome

**17/17 PASS. Decision: `RETAIN_BYTE_BOUND_VALIDATOR_V3`.**

The matrix proves, within scope:

- v2 hash-to-load TOCTOU is reproducible;
- v3 executes the exact bytes whose hash is persisted under the identical source-replacement hook;
- the two-capture semantic validator issues its intended token;
- token-state JSON remains exactly `schema + entries`, schema `authority-ended-durable-token-state-v2`;
- sidecar pins actual validator byte hash + function name;
- matching restart recovers pending;
- duplicate ID rejects;
- consumed state remains consumed after restart;
- changed source rejects;
- wrong function rejects;
- syntax-error source rejects before ledger use;
- missing callable rejects;
- existing token state without sidecar rejects;
- corrupt sidecar rejects;
- sidecar-only initialization crash can resume only with matching bytes;
- the original one-capture bridge can be separately pinned and issue its intended receipt;
- a v1-pinned state refuses v2 reopen.

Formal result SHA-256: `1cc46fd0d2436accd4406dc77e14c972c0ba641244910d87672463a8601df13a`.
Independent retained audit: **PASS**.

## Interpretation

Validator *source-path identity* is weaker than validator *executed-byte identity*. v2 was sufficient only if the source file was guaranteed not to change between the two reads. v3 removes that assumption from this boundary by compiling and executing the exact bytes it hashed.

This still does not make arbitrary validator code trustworthy. A pinned validator may contain harmful top-level Python code. The claim is only that the bytes recorded in the session contract are the bytes executed to construct the callable.

## H / T / D / C / U

**H.** Hashing and executing the same in-memory byte string closes the v2 hash-to-load TOCTOU while preserving existing durable-token semantics and state format.

**T.** Frozen 17-case offline matrix. Deterministic source replacement after the hash read is applied to v2 and v3 under identical conditions, followed by restart, corruption, function-selection and v1/v2 compatibility controls. Zero formal retries.

**D.** **RETAIN_BYTE_BOUND_VALIDATOR_V3** because v2 executes B while pinning A, whereas v3 executes A while pinning A, and all retained durable-state fail-closed gates pass.

**C.** If validator source itself imports mutable external modules, those dependencies are not covered by this single-file byte pin. The current bridge semantic fixture is self-contained, but a general validator dependency closure would require a broader artifact/module identity contract.

**U.** Offline deterministic fault injection, trusted Python interpreter/runtime, single-writer local filesystem. No hostile kernel/filesystem, code-signing, sandboxing, live GUI, model, network, power-loss or durable-submit claim.

## Next smallest experiment

Do not expand directly to a dependency-graph packager unless a real validator needs external mutable imports. For the current self-contained bridge validator, the remaining blockers to live Inkscape composition are elsewhere:

1. PR #168's live ABI evidence still lacks reconstructible executed-source provenance and needs a correctly source-frozen rerun/version;
2. the live receipt builder must expose the already-retained runtime identity rule `authority_end_id = interruption.intent_token`;
3. the live durable-token path should use this byte-bound validator contract rather than process-memory monkeypatching.

After those are closed, run one same-application crash-after-send/reconcile block with motor/capture policy unchanged.
