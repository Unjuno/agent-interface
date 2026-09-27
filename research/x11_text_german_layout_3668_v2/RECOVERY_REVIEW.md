# Issue #3741 German XKB delivery v2 — integration recovery review

## H — hypothesis

The frozen X11 text planner and private-Xvfb XTEST path would deliver the exact formula `=B2*A2` under the standard German XKB layout, while rejecting unsupported text before emitting input.

## T — evidence checked

The retained allocation is `issue3668-german-xkb-text-v2`, with the frozen backend, probe, auditor, and protocol identities recorded in `FREEZE.json`. All four Git blob identities match the frozen values. The protocol specifies three German rows and one US control. The run was a WSL-host/private-Xvfb fallback, not Docker/container evidence; no application task, model, host display, or user input was involved.

The stored `results/AUDIT.json` reports `FAIL_AUDIT`: each German row decoded `)B2}A2` instead of the frozen formula and recorded receiver events before the single valid delivery. The US control decoded the expected formula. A read-only local rerun of the retained auditor reproduced the failure for de-02 and de-03, but could not complete the four-row audit because `results/de-01.json` is absent. The stored audit summarizes de-01 and includes a row hash, but the corresponding raw row is not present in this branch; that summary is not a substitute for the missing raw evidence.

## D — disposition

Preserve this as a scoped negative result and evidence-integrity limitation. Do not call German formula delivery a PASS, and do not claim the full four-row audit was independently reconstructed. The two available German rows consistently demonstrate the wrong decoded string under this frozen setup; the absent de-01 raw and audit failure limit the completeness of the formal record.

## C — controls

The frozen formal run was not repeated, and its retained results, stored audit, source files, and protocol were not edited. The retained auditor was rerun read-only; its output was written outside the evidence directory. The namespace-index update also lists the already-present Issue #4471 STOP directory so the repository's existing workspace-index gate covers current main.

## U — limitations

No inference is made about Calc effects, other X11 servers, other layouts, promoted runtime behavior, or broad text-delivery reliability. Later focused German XKB allocations are separate evidence and do not overwrite or upgrade this allocation.
