# Manifest closure auditor v1

Task: `MANIFEST-CLOSURE-AUDITOR-20260918-001` / Issue #1467.

## H/T/D/C/U

H: Separate inventory closure and local byte/hash closure can reject incomplete retained publication without executing experiment/reconstruction code.

T: Standard-library container only. Exact main snapshot of #1459 inventory/manifest/evidence is frozen in `CASE_SNAPSHOT.json`. One deterministic formal invocation exercises the real snapshot plus complete, missing, corrupt, manifest/evidence disagreement, unsafe-path, duplicate and malformed-SHA controls. Independent result audit follows. No #1459 scientific rerun.

D: PASS iff the real snapshot is rejected exactly for formal parts03..06, complete controls pass, every negative control maps to its exact failure class, source readback remains exact, formal1/reruns0 and independent audit passes.

C: Closure does not establish semantic correctness, archive extractability or reconstruction-script safety.

U: The real snapshot is GitHub inventory evidence only; missing worker-local/unpushed bytes are not inferred or synthesized.
