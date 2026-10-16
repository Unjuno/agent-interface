# T2 X11 A2 — absolute deadline after current-effect receipt wake

Issue #1518. Direct scientific parent #1492.

One mechanism factor changes: after every effect-receipt queue wake, the candidate samples the monotonic clock and refuses acceptance when wake/accept time is at or beyond the existing 8 ms absolute deadline. Receipt schema, observer, fixture, frontier +40 ms schedule, offsets 34/36/38/39 ms, F8 hold 8 ms, app delays 0/3 ms, 16 matched positive pairs, four NO_EFFECT controls, p95<6 ms/max<8 ms gates, and zero-rerun discipline remain fixed.

A positive timeout under strict enforcement is a safe HOLD, not a threshold relaxation. #1494 is a coordination-invalid duplicate and is not pooled.
