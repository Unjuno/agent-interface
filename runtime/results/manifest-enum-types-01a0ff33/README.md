# Manifest enum boundary repair — #6854

On main `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`, JSON lists or
objects in backend `platform.os`, capability `state`, or coordinate-frame
members raised `TypeError` before the contract could refuse them. The exception
escaped `admit_program` and `office_readiness`. The repair checks strings before
set membership/construction. Valid enum values and existing refusal codes remain
unchanged. No broad exception catcher or request coercion is added.

Worker `01a0ff33-df63-7d60-871f-a7ecd2649d07`, policy FINAL-v5.
Related: [#3850](https://github.com/Unjuno/agent-interface/issues/3850),
[#4369](https://github.com/Unjuno/agent-interface/issues/4369) (operation enums;
manifest validation was explicitly excluded there). Ownership is limited to the
three manifest guards, the new regression file, and this additive evidence path.

## Executed evidence

Native Windows / CPython 3.11.9, standard library, sequential processes.
This is ordinary engineering reproduction and regression, not a formal allocation.
The same fixed 77-input corpus was recorded before and after repair:

- 33 invalid JSON enum cases: three fields times eleven values.
- 36 valid OS/frame/state combinations, including permission and unsupported controls.
- Eight frame-list controls, including two mixed unhashable-member cases and one valid multi-frame list.

The independent raw-only audit reconstructs validation, admission and office
readiness without importing the runtime or candidate tests. Before: 14 input rows
produce `TypeError` at each of the three API entry points. After: zero unexpected
exceptions; all invalid manifests refuse and all valid controls match. It rejects
10/10 copied-output corruptions, covering denominator, identity, input mutation,
invalid acceptance, escaped exception, source/fixture identities, permission
promotion and side-effect declaration. Result: `PASS_JSON_MANIFEST_BOUNDARY_SCOPED`.
The auditor is a separate implementation/process by this same author; external
non-author review remains outstanding.

Focused regressions before repair: five methods, 38 subtest errors, exit 1.
After repair, the complete core workflow suite: 70/70 methods, exit 0.
The existing CLI workflow command: 121 methods, 115 passed, six platform-specific
skips, exit 0 after source closure. Its first two attempts both had the same one
`FileNotFoundError` because the initial sparse checkout omitted the nested X11
package; those failures are retained. A sparse-add command with an unsupported
`--no-cone` option failed before the second attempt; using the already configured
sparse mode and adding the backend Python files resolved the local source issue.
No production change was made for that setup failure. Core compilation and the
side-effect-free core doctor returned exit 0. `git diff --check` passed.

## H / T / D / C / U

- H: type-first guards preserve the invalid-manifest refusal boundary for JSON inputs.
- T: test-first reproduction, the fixed before/after matrix, raw reference audit,
  corruption controls, and the applicable core/CLI workflow commands above.
- D: every declared row and input must reconcile; invalid values refuse through
  the contract, valid admission/readiness stays compatible, and every corruption
  is rejected. The recorded evidence satisfies this bounded gate.
- C: broad TypeError catching would obscure unrelated errors; these local guards
  preserve the established ContractError path.
- U: sequential JSON data only. Arbitrary Python objects/subclasses, concurrent
  mutation, native execution, live task effects, real-time performance, model
  efficiency and product readiness are outside this result.

No backend, user input, model, GPU, Docker/WSLc, lease or consumed experiment was
used. The six CLI skips do not establish foreign-platform behavior. Doctor
output is host discovery only. No shared resource lock was acquired. The common
fleet deadline and review committee are not established here and were not reset.
Main integration requires FINAL-v5 content review, current-base combination review
and conditional application; local PASS is not evidence that those gates passed.

## Reproduce without overwriting retained outputs

From the repository root, select fresh absolute output paths on the host:

```sh
python -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -m compileall -q runtime/core_v1
python -m runtime.core_v1.doctor
python -m unittest -v runtime.cli_v1.test_attempt runtime.cli_v1.test_cli runtime.cli_v1.test_review runtime.cli_v1.test_observe runtime.cli_v1.test_golden_v3 runtime.cli_v1.test_receipt runtime.cli_v1.test_receipt_motor_state runtime.selector_v1.test_selector runtime.motor_state_v1.test_adapter
python runtime/results/manifest-enum-types-01a0ff33/run_matrix.py /fresh/path/matrix.json
python runtime/results/manifest-enum-types-01a0ff33/audit_matrix.py /fresh/path/audit.json
```

The matrix runner exclusively creates its output. The auditor checks the retained
before/after records and exclusively creates a new audit receipt. Neither launches
a backend. A rerun from a Git checkout can have different source-byte hashes due
to LF/CRLF conversion; source identity is reported explicitly. SOURCE_MANIFEST
records the exact local source hashes used for each matrix; publication manifest
records canonical staged Git bytes separately. The fixture was generated and
fixed before the patch/matrices and is preserved verbatim.

Public log copies replace only the private checkout prefix with `<checkout>`.
Original logs remain in the author's private workspace. Every public byte hash is
listed in PUBLIC_MANIFEST.json, excluding that manifest itself to avoid recursion.
