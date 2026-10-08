# Issue #3066 v3 formal result

**Disposition: `FAIL_SAFETY_GRAPH_HIDDEN_DEPENDENCY` under the frozen auditor.** The complete 14/14 allocation ran once from row 0 on current-main source. The raw-only audit recorded two independently observed late supervisor releases during the injected cleanup-failure schedule: F8 returned to up at 71.177 ms and 70.903 ms after the 150 ms lease deadline, exceeding the frozen 50 ms grace by 21.177 ms and 20.903 ms. Both terminal samples were up; the recoveries were still late.

The frozen graph gate also found an unlisted Xvfb abstract-namespace socket alias in every cell (`@/tmp/.X11-unix/X610` through `X623`) and 55 socket FDs whose peer/path could not be reconciled. The named aliases are exposed by the declared Xvfb process, so these rows establish a graph-manifest/reconciliation failure; they do not show that an extra process owned the display. The auditor preserves the preregistered hidden-dependency disposition and was not retuned after observing the data. The two late releases independently establish a safety failure even if the alias classification is treated as a manifest omission.

All 14 rows were present and unique. The unknown-dependency control typed STOP before creating a worker in both configurations. Independent terminal key-state samples were up in all 14 rows. Display-stall releases were 42.37 ms and 42.30 ms after the lease deadline, within the frozen 50 ms grace. The target-replacement case lost the application-local release event but retained the independent X-server key-state evidence; this is not counted as a task-effect observation.

The test used the exact current-main `runtime.cli_v1.api.dispatch` facade, actual `X11RuntimeSession` and `X11Backend`, and an independently observed application under pinned Xvfb, bare and Openbox. Formal container exit was 0; the independent auditor exited 2 for the frozen FAIL result. No formal retries, row replacements, pooling, or post-result changes were made.

## Scope

The actuator was synthetic F8 under one pinned Linux Xvfb/XTEST image. This tests neither physical HID nor general GUI safety, application task success, other operating systems, nor production behavior. The result supports keeping Issue #3066 open: timely recovery failed for the injected cleanup path and complete socket-peer reconciliation remains unmet.

## Reproduction

Use the frozen command and image recorded in `research/integration/safety_graph_live_x11_3066_v3/FREEZE.json`. `RAW.json` and `AUDIT.json` are preserved without modification in this result directory. The frozen source/gate manifest remains separate from these post-run outputs.
