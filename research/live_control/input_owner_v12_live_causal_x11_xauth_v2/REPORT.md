# #1261 first formal outcome

Decision: **`FAIL_LIVE_LINEAGE_COMPOSITION`**. This is the frozen first outcome; formal invocations1, reruns0.

All 12/12 private-X11 sessions produced exactly one application-visible F8 KeyPress and KeyRelease and independently finished with F8 physically UP. Baseline application behavior passed6/6; candidate application behavior passed6/6. Cleanup left no private X11 socket residual. Candidate v12 produced `CONFIRMED_PHYSICAL_DOWN`6/6 and `CONFIRMED_PHYSICAL_UP`6/6.

The formal runner nevertheless raised `TypeError: can only concatenate str (not "int") to str` in all six candidate rows before it recorded adapter composition. The frozen auditor therefore reports `FAIL_LIVE_LINEAGE_COMPOSITION`; that decision is retained unchanged.

A read-only posthoc diagnosis over the retained measurements and exact retained adapter composes all six candidate DOWN/UP pairs successfully, with same actuation id6/6, exact owner/intent/key lineage6/6 and authority false6/6. Static source localization identifies runner line102: `adapter=load_module('adapter_'+str(pair)+'_'+position,deps['adapter'])`; formal `position` is an integer, whereas the excluded construction harness passed a string position and therefore did not expose the defect. This posthoc result localizes the next one-factor harness repair but does not convert or rerun the frozen FAIL.

Scientific scope: private Xvfb/Tk on one host and F8 only. No model/provider/network/real desktop/MAP01/shared-runtime mutation. Cross-process clock comparability and production authorization remain outside this result.
