# Control-supplement construction record — v1

The frozen v1 supplement was not executed. Preflight found that a broad wait-time edit also changed the candidate branch from the original 1.5 s cap to 3 s, and the pair assembly still called `run_case(True)` instead of loading the retained candidate result. Both would violate the frozen supplement. The v1 freeze/script remain unchanged; a corrected version is frozen separately before the baseline-only execution.
