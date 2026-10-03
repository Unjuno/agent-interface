# Supplementary data-only sample-completeness review

Original consumed producer and audit files/first results remain unchanged. The
separate sample_custody.py gate matches each EAGAIN/EOF read-loop ending within
the recorded ACK decision window to exactly one retained poll sample, in order.
The first poll and the decision poll must both be present; duplicates, gaps,
boolean read counts and inconsistent clock ordering are refused.

Four corruption cases failed against the initial no-op supplementary gate;
implementation now passes its three tests, including the actual six ACK rows.
Original ACK-target rows1/2/4/7 have2/2/3/2 poll samples; wrong-target rows5/6
have237/421. Each count matches its original read-loop endings in the decision
window. No producer/auditor/GUI/input replay is performed. This closes a retained
review gap, not a post-consumption change to the frozen scientific audit.

GitHub PR content creation remains deferred after the recorded 18:00:11 UTC403.
No new creation retry is needed merely because this local review completed.
