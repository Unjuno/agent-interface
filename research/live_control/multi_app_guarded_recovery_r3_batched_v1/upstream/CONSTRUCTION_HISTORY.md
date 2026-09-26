# Construction history — Issue #1769

No formal allocation was consumed during construction.

The first complete 3-cycle construction passed the preregistered R3 gates without a scientific-source repair. It also exposed a descriptive X11 lifecycle fact: raw Chromium window IDs were reused across non-consecutive process generations (`6291459 -> 16777219 -> 6291459 -> 16777219`). Adjacent replacement IDs still differed and each old window was gone before rebind, so this did not violate the frozen R3 gate. No generation/ABA gate was added posthoc; the observation is retained as a limitation and possible separate successor question.
