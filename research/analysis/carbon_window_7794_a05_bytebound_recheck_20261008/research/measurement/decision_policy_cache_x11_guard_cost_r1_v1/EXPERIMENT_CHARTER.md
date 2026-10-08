# Decision-policy cache private-X11 guard cost R1

Parent #1155; predecessor #1163/PR #1168.

H: with identical visual state semantics and XGetImage primitive, a 32x32 current-state ROI can preserve action-time guard semantics while reducing p95 acquisition cost by >=50% versus a 320x240 full-frame guard, with ROI p95 <1ms and hard-invalidation-to-stop p95 <=10ms at 5ms action cadence.

T: 24 matched pairs, private Xvfb 640x480x24, one 320x240 X11 window with a centered 32x32 state sentinel; FULL_FRAME_GUARD vs ROI_GUARD changes only capture extent. Each case has VALID, one between-slot AMBIG interval, VALID, then persistent HARD. Fixture subprocess owns visual transitions and monotonic timeline. No OS/task input; candidate effects are logs only. One formal invocation, reruns0.

D: exact gates from Issue #1172: classification/effect safety, 24/24 completion, ROI p95/p99 <1/2ms, ROI/full p95 ratio <=0.50, stop p95 <=10ms, schedule lag p95/max <=2.5/10ms, fewer ROI bytes every pair, no host-noise trigger, integrity/audit PASS.

C: sentinel is favorable to ROI; Xvfb is not production compositor; a positive result motivates cheap admission evidence but not token/end-to-end claims. Transition-overlap implies a later fencing question.

U: single Linux private-X11 synthetic fixture only.
