# A12 single-owner button-event observation successor

A11 is preserved as `STOP_HARNESS_X11_EXCLUSIVE_EVENT_MASK`: keys and Button1 were admitted and the pointer mask saw Button1 down, but X11 rejected duplicate ButtonPress/Release selection with BadAccess before session death. A12 retains the two-key plus Button1 recovery question and gives the exclusive ButtonPress/Release event mask only to the independent observer; the focus client selects keyboard events only. All other gates are unchanged.

Fresh absent output leaf, one candidate invocation, no retry. PASS requires independent key/button down/up, session SIGKILL, verified matching fsynced owner receipt with empty keys/buttons, clean service exit, and supervisor-requested clean Xvfb exit.
