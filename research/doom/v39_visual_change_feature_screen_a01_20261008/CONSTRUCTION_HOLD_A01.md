# Construction attempt 1 — HOLD

The first invocation of `python run_screen.py` exited 1 before computing any feature because the candidate assumed the retained screenshots were 1280x720. The actual PNG dimensions are 1280x800. No measurements or disposition were produced by this attempt. It is retained as a harness setup failure; the correction changes the expected dimension only. The fixed viewport crop remains `(322,181)-(960,583)`, within the observed game window.
