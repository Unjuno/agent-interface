# #7188 sparse single-mint current-main revalidation

Disposition: `PASS_SCOPED` for local input validation only; no merge or branch
deletion is authorized by this report.

## H / T / D / C / U

- **H:** On current main, `Array.prototype.every` skips absent array slots, so a
  two-element sparse coordinate pair can pass `Number.isSafeInteger` validation
  and reach host dispatch. The pair must instead validate both indexed values.
- **T:** Call `createPrimaryCaller(..., 'guarded-local', {}).mint()` once with a
  two-element point whose first slot has been deleted and a dense valid region.
  Expect local rejection and zero host calls. The fixture returns a valid
  `interface_guarded_mint` envelope if dispatched, preventing response-shape
  errors from masquerading as the validation failure.
- **D:** Main snapshots `11445a7ca200404ddc80bf7ebb1dbef86eb059de` and, after
  unrelated fast-forward updates, `9146507c2689da7d4444d8febda848fa7dd4bcd1`;
  predecessor PR #7188 head `0f53b3e32f20e7b270643f1dc87baf66919ef7c3`. First ran the new
  regression against unchanged main: it failed with “Missing expected
  rejection,” demonstrating that the sparse pair passed validation. Applied
  the one-expression `Array.from(value).every(Number.isSafeInteger)` correction
  and reran the regression and documented `runtime/host_v1/test_*.mjs` suite.
- **C:** Dense safe pairs and all existing host_v1 behavior are covered by the
  existing suite. `mintMany` already uses `Array.from`; this change does not
  alter its path. No original #7188 archive, raw evidence, or historical result
  was changed.
- **U:** Local synthetic host only. This does not establish a live backend,
  physical input, application effect, performance, or task-quality result.
  The original PR remains OPEN/DRAFT with no approvals; its prior checks and
  votes do not transfer to this current-main revalidation. Independent review
  and the repository's required merge gates remain outstanding.

## Executed verification

Environment: macOS, Node.js v26.7.0. The initial regression was observed RED on
unchanged main and GREEN after the correction.

```text
node --test runtime/host_v1/test_primary_mint_sparse_rescue.mjs
  PASS 1/1

node --test runtime/host_v1/test_primary_caller.mjs
  PASS 40/40

PRIMARY_FAILURE_EVIDENCE=<fresh mktemp directory> \
  node --experimental-vm-modules --test runtime/host_v1/test_*.mjs
  PASS 217/217 (including host_timing integration and required explicit-evidence tests)

git diff --check
  PASS
```

The VM-modules option is documented by `test_primary_terminal_failure.mjs`;
`PRIMARY_FAILURE_EVIDENCE` is required by `test_primary_stdio_failure_order.mjs`.
The entire host_v1 suite was rerun after each main fast-forward, including the
latest recorded snapshot. These are local tests; no claim is made about GitHub
Actions.
