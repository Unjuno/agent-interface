# #17 GIL cancellation construction C01

First4 macOS native construction cells: **HOLD_ORDER_OR_CONTRAST**. External cancellation delivered during an observed300ms ctypes call. Dedicated safety thread closed its owned dummy /dev/null FD after19,292/131,750ns for CDLL and250,017,000/259,272,083ns for intentional PyDLL. All child exits0, dummy FD closures and thread joins completed.

One held-GIL closure occurred before the Python call-end marker, contrary to the fixed gate. The marker samples Python control AFTER actual native return; another runnable thread can act before it. Preserve HOLD and this instrumentation limitation. No replay, post-result threshold relaxation or success claim. All four sends were inside the recorded start/end bracket, which does not authenticate exact native entry/return instants.

Source/fixed gates and independent saved-only auditor precede first collection. Collector24278 and auditor24328 exit0 with native receipts. Audit exit0 means consistent HOLD, not scientific PASS. Source ends .py.txt and is inert; no runtime, workflow, automatic test-discovery or existing evidence changed.

Scope: macOS Homebrew CPython/ctypes intentional retained-GIL foreign-call comparison, not Linux/container experiment, production defect, process-isolation comparator, physical input release, task effect, hard deadline or general reliability/performance claim. PyDLL is an intentional stress control; official documentation recommends it for Python C API, not arbitrary libc use: https://docs.python.org/3/library/ctypes.html#ctypes.PyDLL . Prior #6996/#7049/#7079 allocations unchanged.

Operational private workspace prefixes are literal display projections in PUBLIC_PROJECTION.json; original byte hashes/local retention remain separate. Raw child measurements/freeze/probe/auditor are unchanged. Next method must independently observe native return or prospectively choose a directly observable response measure, with distinct source/gates/allocation and actual isolated container ownership. C01 is consumed4/4; do not replay it.
