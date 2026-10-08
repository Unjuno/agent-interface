# Issue #4231 preformal plan

Allocation: effect-receipt-time-separation-4231-20260923-01

## H
Effect commit time and terminal receipt delivery time are distinct. An effect committed by the owner before the 120 ms task deadline remains on-time even if its receipt is delivered later; receipt-arrival-only classification will falsely label that case late. Owner-commit classification requires identity-bound journal evidence; an unverified claimed commit timestamp remains UNKNOWN.

## T
Three policies x four schedules x three repetitions =36 fresh owner cases. Separate owner process is the only writer of fsynced effect bytes and owner journal. Common CLOCK_MONOTONIC domain. Deadline120ms. Schedules: commit60/receipt80; commit60/receipt170; commit150/receipt170; no commit/receipt80. No model, GUI, OS task input, experiment network, or user data.

## D
PASS_EFFECT_RECEIPT_TIME_SEPARATION_SCOPED requires all36 rows; receipt-arrival comparator misclassifies all3 on-time/late-receipt cases; owner-commit policy correctly classifies those3 ON_TIME, all late commits LATE and no-commit NO_EFFECT; unverified commit field always UNKNOWN; authority/retry_authority always false; owner exits0; raw audit errors=[]; >=10 coherent corruption controls reject.

## C
Cooperative owner and same monotonic clock domain. fsync return is fixture commit, not power-loss durability. Directed delays are not natural latency distributions.

## U
No model/task utility, GUI, distributed clock translation, authentication, external service, power-loss durability, hard-real-time, token/latency benefit, or product claim.

Construction-01 retained STOP/HOLD: common start was sampled before owner process startup, contaminating the timing treatment. Construction-02 changed only the timing origin to after owner READY and passed12/12; construction is excluded from formal.
