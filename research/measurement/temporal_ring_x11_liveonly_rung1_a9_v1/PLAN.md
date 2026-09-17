# A9 fresh real-X11 temporal-ring Rung1 integration

Issue: #1095
Task: TEMPORAL-RING-X11-LIVEONLY-RUNG1-20260918-009
Base: 51d9f5b3b534286f9a4ac50e6a2321e919300a0d

Scientific H/T/D/C/U are unchanged from #1084. #1084 is coordination-invalidated and contributes zero formal rows.

H: already-retained A7-style 20 Hz fixed-ROI history should answer two-frame historical requests without new acquisition; live-only JIT must wait for a future-equivalent 100 ms span.
T: six fresh counterbalanced pairs, four requests per arm, ROI [80,60,160,120], 76,800-byte normalized payload, 20 Hz, 500 ms ring, 400 ms first request, one detached formal invocation, reruns0.
D: PASS iff ring p95<5 ms, JIT median>=90 ms, paired median delta>=85 ms, role/source/boundary/capture/authority integrity all pass.
C: replay-capable sources can erase the distinction; scheduler jitter may widen JIT wait.
U: private Xvfb/Tk only; no model/task/production claim.
