# V15 lazy-Pillow import successor A05 — PIL-blocked closure probe

A04 passed the full synthetic fake-X suite, but its runtime contained Pillow; that result cannot show whether the one-import relocation actually removes the import-time PIL dependency. A05 keeps A04's exact tree, source closure, candidate patch, test list and runtime, adding only a frozen process-local import finder that rejects `PIL` and `PIL.*` before unittest imports candidate modules. The installed Pillow package is not changed or removed.

## H/T/D/C/U

- **H:** The one-import relocation alone is sufficient for the selected wrapper/test chain to import and run when all PIL imports are unavailable to the Python process.
- **T:** Materialize all immediate-child Python modules from the five roots in RUN_PLAN.json using virtual merge tree `78b8636f08bef691944da8bb536437586f0d116a`; apply only the single import relocation; copy the committed `NO_PIL_SITECUSTOMIZE.py` byte-for-byte to the scratch root so Python imports it before unittest; execute each of the seven frozen modules once normal and once optimized.
- **D:** PASS only if each mode completes 47 tests with zero failures/errors and blocker is confirmed active. FAIL_REMAINING_PIL_IMPORT if a candidate/test module raises ModuleNotFoundError for PIL before reaching all assertions, demonstrating the single relocation is insufficient. STOP for any other missing dependency, failed blocker activation, or runner/setup issue. Preserve both first outcomes and never retry.
- **C:** The A04 pass may rely on other top-level PIL imports in inherited session or observation modules; blocking PIL can distinguish that from the relocated import itself. Optional libraries may catch ImportError, so successful import does not prove every PIL use is absent, only this tested chain's import behavior.
- **U:** The meta-path blocker models import unavailability within this process, not a clean operating-system/container image. Even PASS remains synthetic regression evidence; it cannot prove no-Pillow image capture, native X11, live threat response, application effect, latency, or Issue #59 acceptance.

This is bounded ordinary regression work, not a formal allocation. No package install/uninstall, network, GUI, X server, game, model, native Xlib or physical input is permitted.
