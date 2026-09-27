# Issue #2918 allocation 04 — independent audit-only successor

## H/T/D/C/U

**H.** The immutable 12-case allocation-03 output may satisfy Issue #2918's
scoped decision gates when every API receipt, artifact, target binding, intent
epoch and terminal disposition is independently reconciled from retained
bytes. Allocation 03's frozen auditor STOPped before emitting a result due to
a code defect; its raw bytes remain unchanged.

**T.** Run only the new frozen independent auditor on
`issue_2918_live_certificate_v3/allocation_03_raw/`. Do not start Xvfb, call
the runner/API, regenerate outputs, or edit predecessor data. Mount the raw
input read-only and a separate report directory writable. The auditor checks
all 12 fixed cases; verifies PNG hashes/pixels, duplicate contradictory
sensor, partial region, stale age, capture intervals, observation IDs, XIDs,
binding and intent lineage; independently recomputes certificates and branch
terminal outputs; and verifies zero authority/input. This is a new audit-only
allocation, not a rerun of allocation 03's failed auditor.

**D.** PASS the retained allocation-03 experiment only if this independent
auditor exits zero, writes a durable `independent_audit.json` outside the
read-only raw input, and verifies every frozen gate. Any assertion, missing
evidence or output failure is HOLD/FAIL. Exactly one audit invocation; no
second attempt or source edits after start.

**C.** OrbStack Docker, immutable linux/arm64 image, `--network none`,
read-only repository/raw evidence, separate writable report mount. No GUI,
Xvfb, API observation, model, input, provider or external network is invoked.
The scope is the private fixture and public observation boundary only.

**U.** Whether the allocation-03 retained bytes independently satisfy the
gates. Even a PASS cannot establish real-application effect, reduced
end-to-end observation cost, or production readiness.

## Frozen inputs

Allocation-03 raw output and checksum list are committed under
`research/integration/issue_2918_live_certificate_v3/allocation_03_raw/` and
`RAW_SHA256SUMS.txt`. The exact corrected auditor SHA, image ID, mounts and
one-shot command are in `SOURCE_FREEZE.json`. Predecessor runner outputs,
source and STOP/HOLD reports remain unchanged.
