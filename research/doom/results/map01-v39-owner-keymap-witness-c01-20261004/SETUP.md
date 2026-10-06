# Construction environment setup

The selected task-owned OrbStack guest was already preserved from the stopped #59 telemetry work. I started only that guest for this separate construction control. Host snapshot before start showed 64 GiB RAM with about 22 GiB free; several unrelated guests were running, so no other guest was touched.

Fresh preflight found Xvfb installed but Python-Xlib absent. `unshare -n true` failed with `Operation not permitted`, so network namespace isolation is unavailable in this guest. To make the planned local Xvfb control runnable without changing the guest's system Python, I created `/tmp/v39-keymap-c01-venv` and installed the pinned packages `python-xlib==0.33` and `six==1.17.0`. The dependency download completed before freeze. The candidate itself performs no network requests; Xvfb uses a private display number and `-nolisten tcp`. The absence of network namespace isolation is retained as a scope limitation.

`ENVIRONMENT.json` captures the post-setup runtime and namespace limitation before candidate invocation.
