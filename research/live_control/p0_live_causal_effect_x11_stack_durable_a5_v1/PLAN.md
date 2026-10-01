# #1324 durable faulthandler transport

H/T/D/C/U are frozen in Issue #1324.

Exact parent science runner and faulthandler-enabled case child are byte-identical to #1318. The only harness factor is child stdout/stderr transport: open durable files before launch and pass their file descriptors directly to subprocess.run. Keep the 5s dump, 8s timeout, Xvfb lifetime, F8/150ms, scorer, clock/provenance gates and schedule unchanged.

No live X11 before an explicit #60 grant. Construction first; any incomplete session stops the allocation and the durable logs are the outcome.
