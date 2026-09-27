# PLAN — Issue #4167 safety-plane X-server stall recovery v1

Allocation: `safety-xserver-stall-recovery-4167-20260923-01`
Formal status at freeze: **0/6**.

## H
While the owned X server is SIGSTOPped, a cleanup-only watchdog may have a release request pending but must not claim verified release. After SIGCONT of the same server, the watchdog should complete exactly one KeyRelease and verification. With no watchdog, the held key should remain down through the +250 ms measurement until labelled fixture cleanup.

## T
Fresh private Xvfb/Tk/XTEST case. Press F8; SIGSTOP Xvfb at press+50 ms; candidate receives cleanup at +75 ms; inspect for any receipt at +150 ms; SIGCONT at +175 ms; measure independent XQueryKeymap and app events at +250 ms. Arms: NO_WATCHDOG and PENDING_WATCHDOG. Three matched pairs, six fresh first cases, alternating order, one case per outer invocation. Fixed displays 580..585. No same-ID rerun/replacement/extension/tuning.

Formal schedule: f01 NO_WATCHDOG :580; f02 PENDING_WATCHDOG :581; f03 PENDING_WATCHDOG :582; f04 NO_WATCHDOG :583; f05 NO_WATCHDOG :584; f06 PENDING_WATCHDOG :585.

## D
PASS_XSERVER_STALL_RECOVERY_SCOPED only if all6 complete and: candidate pre-resume receipt false3/3; verified_ns >= SIGCONT3/3; one candidate F8 press/release and terminal up3/3; cleanup-only/no-task authority; baseline down at +250ms3/3 before parent cleanup; baseline final neutral after labelled cleanup; candidate SIGCONT->verified median <=25 ms, max<=60 ms; frozen source exact; independent audit error0; >=6 copied-evidence corruptions rejected.

FAIL_FALSE_RELEASE_CONFIRMATION for any candidate confirmed-release evidence before SIGCONT. FAIL_RECOVERY_RELEASE if candidate remains down at measurement. HOLD_NO_XSERVER_STALL_DISCRIMINATOR if baseline auto-neutralizes across pause/recovery. Missing source/process/denominator evidence is STOP/HOLD.

## C
SIGSTOP/SIGCONT is one same-process X-server unavailability model. Scheduling and resume latency can affect measured post-resume time. XTEST/XQueryKeymap are X-server evidence, not physical HID telemetry.

## U
No new-server restart, host crash/power loss, physical/uinput backend, cross-platform, hard release deadline during outage, model/task benefit, production promotion, or failure-rate estimate.
