# F02 repeated-wait construction FAIL

Sourcee7ab04be3, candidate unchanged frombb65ffd31. New realpipe repeatedwait
expectations are distinct from earlier4caseconstruction and consumedF01allocation.
FixedGitarchive host/guest SHA both
aa9845d71141a14458daa7b8fbc35f34cd1ffd4f8a297fc13850351d84f52e9a.
OwnVM/frozenimage/isolatedconfiguredlimits sameF02construction; freshcontainer
f02-repeat-wait-red-v1. Executed python3 -B -O -W error -m unittest discover -v.
Firstresult6tests,4passed/2failed,0.745s; exit1/noOOM,23:03:08.440841073–
23:03:09.442873102Z. Complete stderr/stdout+State retainedmethods/REPEAT-WAIT-RED.log.

Both test_repeated_wait_does_not_lose_eof_state and
test_repeated_wait_does_not_lose_parser_failure fail atwaitattempt2:
expectedtypedfailure, actualTimeoutError. Singlefailuremarker consumed byfirst
wait leaves deadreader/livechild/emptyqueue. No persistent failedstate yet.
Oldsinglewait4PASS is unchanged but doesnotqualify repeatedconsumerrecovery.
Nextcandidate must preserve failurecause across subsequentwaits without stealing
alreadyqueued legitimateevents or misclassifying normal completedterminal.
This firstFAIL remainsretained; any repair gets newconstruction/freeze, not
rerun/relabel ofconsumednativeallocations. No fullcontroller/game/adoptionclaim.
