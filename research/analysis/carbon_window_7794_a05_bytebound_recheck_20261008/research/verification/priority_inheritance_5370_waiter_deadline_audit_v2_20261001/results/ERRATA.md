# Errata — construction test count

The audit-v2 construction suite contains **8 tests total**: one positive test accepting the hand-authored valid fixture, plus **7 negative mutation controls** (missing row, duplicate row, altered stale time, removed schedule event, late completion, inheritance overrun, and unauthenticated urgency affecting priority).

An earlier conversational update described these as “8 corruption controls”; that count was incorrect. The test result remains 8/8. No formal audit, frozen source, raw output, or audit result is changed.
