# WSLc Calc post-release observation A09

One predeclared exploratory no-model fixed-layout successor to A08 at candidate 1b806a086951c6beca6725771fd6c1066d47b9a3. Its test-only private `_Adapter` subclass waits 500 ms after a completed action with verified release before making a new effect observation; the wait is outside the native input guard. It has no cancellation polling during that wait and is not a production API or a hard timing guarantee. The caller uses a manually selected menu-region window anchor and a constant ready predicate, which do not independently identify the destination cell.

The graph reported TASK_SUCCEEDED with one completed transition. The retained receipt orders action acceptance and verified release before the ~500 ms test-only delay and fresh effect capture. OCR calls returned an initial blank then 29, 31 and 899; the independent saved-XML scorer confirmed the expected formula and value without extra cells. Native release, separate key/button readback and exact-ID container cleanup were neutral/complete. No verified bridge-close receipt was produced. All raw logs, OCR attempts, images, conditions, workbook and hashes are retained.

One sequential case does not prove safe general settling, automatic recovery, model/token efficiency, reliable OCR, a matched speedup or MAP01 completion. No original failed operation was replayed.
