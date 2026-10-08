# Issue #2769 live X11 pixel VERIFY transfer v1 — retained HOLD

Disposition: **HOLD_FROZEN_CORRUPTION_CONTROL_INCOMPLETE**.

## Formal first outcome

The single frozen 18-session allocation completed with exit 0. Two installed real X11 applications (xterm and xmessage) were exercised across nine classes each. The raw-only auditor reports PASS_RAW_AUDIT with 18 rows, candidate/oracle mismatch 0, candidate unsafe local resolutions 0, candidate local resolutions 6, and lineage-blind naive unsafe local resolutions 10.

Current TRUE/FALSE cases matched in both applications. Stale-after-newer, timeout-before, timeout-after, replacement, malformed/truncated, and delayed-verifier evidence never became candidate LOCAL_TRUE/LOCAL_FALSE. Live EFFECT signatures were captured from the running applications; no RGB signature constants were authored.

## Why overall status is HOLD

The frozen corruption-control program rejected 7/8 mutations. The eighth mutation edited replacement capture identity but left an independent generation mismatch, so the raw auditor correctly continued to classify the row stale and therefore did not reject that ineffective mutation. The frozen requirement was >=8 rejected controls, so the formal allocation is not promoted to PASS.

A separately versioned, postformal read-only controls_v2 replaced only that ineffective challenge with an expected-byte-count corruption. It rejects 8/8. This diagnoses the audit-test defect and does not rewrite the frozen 7/8 first control result or rerun any X11 session. All six frozen source hashes remain exact after formal.

## Construction failures retained

Construction-only failures before freeze included an outer tool timeout, missing default XAUTHORITY, two capture implementation defects, and a gzip API misuse. construction-07 then completed four excluded current TRUE/FALSE rows with candidate/oracle mismatch 0. None are pooled into formal.

## Scope

Provided Linux x86_64 execution container, CPython 3.13.5, Python-Xlib 0.15, private Xvfb with TCP disabled, xterm and xmessage. Docker CLI/image identity unavailable. No XTEST/keyboard/mouse task input, model/provider, external network experiment, user desktop, shared runtime/default or token/task-speed claim. xmessage and this first-rung xterm state changes use fresh application processes, so this is a lineage/currentness transfer boundary rather than arbitrary same-window application semantics.

Formal RAW SHA256: `ec5938107008fc355f41caa721112d20b2c5d987f821934a5ef4927c7ef22756`.

Parent #1847/#1870 STOP evidence remains unchanged. #2769 remains open because the frozen acceptance gate was not fully satisfied; do not rerun this consumed allocation. A future allocation, if justified, must be separately frozen and should preserve this HOLD.
