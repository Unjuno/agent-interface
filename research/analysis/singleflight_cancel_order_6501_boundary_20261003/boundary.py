def ordered_verdict(events, caller, truth):
    cancelled = False
    for event, timestamp_ms, sequence in sorted(events, key=lambda e: (e[1], e[2])):
        if event == "cancel_" + caller:
            cancelled = True
        elif event == "return":
            return "CANCELLED_WAITER" if cancelled else "ADMISSIBLE_" + truth
    return "UNKNOWN"
