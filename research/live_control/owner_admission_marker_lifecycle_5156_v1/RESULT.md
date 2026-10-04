# Result

The exact PR #7376 wrapper at `0f112dcae1e3b108ae2eecddebd95b829b8fbffa`
passed 64 asynchronous cancellation/re-admission cycles against the real v10
owner queue with fake Xlib/XTest. Each cycle recorded one verified empty
`owner_release`, produced the expected KeyPress/cleanup-KeyRelease pair, and
left exactly one admission marker for the newest lease. The observed maximum
marker count was one; the final async cleanup remains cached until another
wrapper operation observes it or the wrapper closes.

`audit.py` verified both tested source hashes and the raw outcome/exit receipt.
This is a local construction probe of queue/marker lifecycle. It measured entry
counts rather than bytes or production frequency and does not establish actual
X11, physical input, GUI behavior, latency, or user-visible control.
