# X11 reconnect key-state boundary — Issue #4135

H/T/D/C/U are preregistered on Issue #4135. Formal matrix: 6 schedules x 2 policies x 2 reps = 24 fresh Tk sessions. Primary outcome is exact Entry value after policy decision. All time values are diagnostic monotonic nanoseconds; no timing performance gate.

Variables: `shift_down` boolean X-server logical Shift state; `epoch` opaque observer connection identity; `seq` positive event ordinal local to one observer epoch; `final_value` Unicode Entry content; `rep` finite repetition index. All are dimensionless except diagnostic clock values (ns, SI 1e-9 s).
