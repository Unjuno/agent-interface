# A02 import-closure preflight

This additive preflight diagnoses the A01 frozen-package omission without rerunning A01 or executing candidate behavior. It reads committed source blobs from current upstream main `6f34c5c0c5bc3116d8e7c25f29aa1b92cc4a01b1`, recursively parses static Python imports, and locks every discovered source blob in `IMPORT_CLOSURE.json`.

## H / T / D / C / U

**H.** The A01 startup STOP resulted from an incomplete offline source package. A recursive static scan of the exact V15 measurement entrypoint and its selected V39 backend/Executor/owner chain can identify a complete repository-source closure and its direct third-party import roots.

**T.** Parse `import` and absolute `from ... import ...` declarations in Python ASTs loaded from the exact main commit. Resolve repository modules in the flat `research/doom`, `research/live_control`, and `research/observation_gating` import roots. Lock each included blob ID and report remaining repository-local imports and external roots.

**D.** Scoped PASS requires the reproducible audit to derive exactly the 38 locked files, verify all Git blob IDs and the source commit, find zero unresolved local imports, and reproduce the listed external roots. The audit passed with `PIL,Xlib,numpy,vizdoom`.

**C.** The selected source set follows V15's `session_map01_v12` base, V15-selected release-batch backend and Executor v13, and their static import closure. Flat-module name collisions resolve to `research/doom`, then `research/live_control`, consistent with these scripts' path setup. A separate allocation/candidate is still required to test runtime import behavior.

**U.** This does not import or execute production modules, start a container/display/game, call a model, send input, establish release/query timing, or prove dynamic/native dependency closure. It does not satisfy Issue #59's live threat/recovery gate. The manifest flags these limits; a future candidate needs a new exact source/image/config freeze.

## Reproduction

From the repository root, run:

```powershell
python -B research/doom/results/map01-v39-v15-release-closure-a02-import-preflight-20261005/audit_import_closure.py
```

The checked stdout is retained in `AUDIT.log`. This audit reads Git objects and parses source; it does not import those modules or execute the candidate. A01's first STOP remains preserved in its sibling package.
