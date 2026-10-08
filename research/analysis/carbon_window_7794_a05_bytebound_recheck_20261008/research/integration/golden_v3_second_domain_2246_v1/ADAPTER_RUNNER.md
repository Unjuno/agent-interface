# GTK/X11 golden-v3 bounded runner

`gtk_adapter_runner.py` launches the GTK fixture, obtains its X11 window ID, and invokes the existing `runtime.cli_v1.golden_v3.dispatch_golden_v3` through the existing X11 backend.

It records:

- independent GTK save-effect receipt
- adapter result
- stale-observation refusal
- dispatch timing
- zero model/provider calls

This is a research preflight, not full #2492 acceptance. It does not claim generality, provider utility, or production readiness.

Run from repository root in the pinned GTK/Xvfb container after installing the repository runtime dependencies:

    DISPLAY=:99 python research/integration/golden_v3_second_domain_2246_v1/gtk_adapter_runner.py --out /tmp/gtk-adapter-2492
