# Frozen audit plan — Issue #3903

- Allocation: `issue-3896-dockerdesktop-import-boundary-audit-01`
- Branch: `research/issue-3896-desktop-import-boundary-v1`
- Path: `research/doom/map01_r4_import_boundary_desktop_v1/`
- Frozen source snapshot: `8652f6a3527d55610185d1103b87d5d9fd8fa985`
- Branch parent: `55427ecda1474b43d8a58bbc5714de7285cc8390`

## H / Hypothesis

A side-effect-aware AST walk can independently determine whether the committed `session_entry.py` invokes its experiment while the module is being imported, while distinguishing deferred function bodies and a conventional `if __name__ == "__main__"` guard. This clarifies whether the #3857 STOP is warranted and whether its whole-tree `main` scan over-approximates risk.

## T / Treatment

Read exactly these two base-commit files as source bytes and parse them as AST; do not import either file or any of their dependencies:

- `research/doom/map01_r4_sparse_checkout_successor_2174/import_gate.py`
- `research/doom/map01_v12_physical_occupancy_live_r1_v1/session_entry.py`

The independent implementation distinguishes module-executed calls, class-body calls, `__main__`-guarded calls, and calls confined to deferred function/lambda bodies. Decorators and function defaults are treated as evaluated in the containing module context. Eight fixed in-memory controls cover a deferred call, main-guard call, direct and conditional top-level calls, decorator/default evaluation, a class-body call, and a lambda body. A second implementation independently parses the retained target and controls.

Construction on the collided predecessor branch (not formal rows): (1) an incorrect Docker invocation supplied the image name as its entrypoint and stopped before the container process started; (2) an inline-probe quoting error produced a Python syntax error before its code ran. Neither accessed or imported the target. A syntax check and a seven-control parse probe passed on Docker Desktop before the branch collision was discovered. Successor `construction-01/` passed all eight controls and hash binding. After adding an AST syntax gate for all four audit sources, fresh `construction-02/` also passed all eight controls, all four syntax checks, and exact source/hash bindings under Docker Desktop. Both successor checks demonstrated the separate writable evidence bind while `/source` remained read-only; the target launch was identified at line 18 as module-executed. Neither imports the target.

## D / Decision

`PASS_STATIC_IMPORT_BOUNDARY_SCOPED` only if all eight controls match their frozen classifications, the exact target has an unguarded module-executed `session_map01_v13.main()` call, the independent parser agrees, every hash matches the committed source set and image/base identities, and all execution-endpoint counts remain zero. This supports the historical gate's STOP disposition; it does not claim the target is safe to import.

`FAIL_CLASSIFIER` for any target/control disagreement, `STOP_SOURCE_HASH_MISMATCH` or `STOP_IMAGE_ID_MISMATCH` for provenance errors, and `STOP_SETUP` if the exact local container cannot launch. Formal invocation: exactly one. No retry or reinterpretation.

## C / Constraints

Docker Desktop 28.5.1, Linux/amd64, cached `python:3.12-slim` image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. No pull, network disabled, read-only root and source, dedicated fresh evidence mount, 64 MiB tmpfs, 1 CPU, 768 MiB memory, 128 PID limit, all capabilities dropped, `no-new-privileges`. Only the audit scripts and the two source files are read. No workflow/launcher import or execution, game, model, GUI, input, runtime mutation, or Docker cleanup.

## U / Limits

Static syntax analysis cannot prove imported dependencies are safe, runtime behavior, archival workflow correctness, or any gameplay/product property. This is a narrow audit of AST classification and the source-level import boundary only.
