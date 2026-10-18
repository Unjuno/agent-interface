# Evidence rescue provenance — 2026-10-07

This file records an evidence-only transfer from the open Draft PRs [#6934](https://github.com/Unjuno/agent-interface/pull/6934) and [#6939](https://github.com/Unjuno/agent-interface/pull/6939) onto the current-main rescue branch. It does not replace either source PR or change the disposition of its implementation.

## Exact inputs and scope

- Source #6934 head: `b332fddcd1372e0cbba07c50691c215b20bd5831`.
- Source #6939 head: `f935da17f6b5d7952ba25ddc42af6099669a8c2b`.
- Rescue base: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`.
- The callback-custody package below was compared directly between both source heads and is byte-identical.
- The literal-unknown result package was copied only from #6939. The selected transfer is 238 files / 2,014,544 declared bytes; the source PRs contain additional runtime changes that are deliberately excluded.
- Both destination paths were absent from the rescue base before extraction. No existing main file or historical result was overwritten.

Transferred packages:

- `research/integration/compiled_callback_custody_57_20261003_01a0ff35/`
- `runtime/results/compiled-literal-unknown-01a0ff35/`

## Integrity and execution boundary

The two package `MANIFEST.json` files were checked against every listed path, byte count, and SHA-256: callback-custody 62/62 and literal-unknown 53/53 matched. The nested context-v3 and context-v4-admission checksum lists also matched in full; context-v4's original CRLF checksum file was streamed through CR removal for verification only. No source artifact, checksum file, receipt, or historical result was edited to make that check pass.

The ordinary staged `git diff --check` reports 10,431 CR-at-end-of-line diagnostics because the historical evidence includes CRLF bytes. With `core.whitespace=cr-at-eol`, those are recognized as line endings and 15 remaining trailing-whitespace lines are still reported in archived source/log snapshots. They are intentionally preserved and hash-verified rather than cosmetically normalized; the new provenance note itself passes `git diff --check`.

No archived runner, test module, backend, GUI, or experiment was executed during this transfer. Historical results remain bound to their recorded source, environment, and commands. This archive does not establish current-main source qualification, live GUI/input behavior, task effect, physical release, integrated efficiency, or a new experiment result. The PR-hosted checks on the source PRs are not checks for this rescue composition.

## Source PR disposition

Both source PRs remain open and their branches are retained. #6934 is marked Draft and has a dirty merge state; its body requires two current-digest independent nonauthor approvals, and none is submitted. #6939 is also Draft; its latest recorded current-main note says a guarded-X11 test could not import because Pillow was unavailable and therefore remains STOP/unverified. Its historical approvals do not transfer to a changed head or to this archive.

Accordingly, this transfer preserves reviewable historical evidence only. It does not approve, merge, close, or authorize deletion of either source PR or branch. Any future source integration must follow Issue #57's composition/evaluation priority and satisfy its own current-source, review, and application gates.
