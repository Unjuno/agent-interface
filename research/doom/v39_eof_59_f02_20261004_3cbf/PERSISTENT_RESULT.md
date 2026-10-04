# F02 persistent single-consumer failure state construction

Candidate12dc76d30 follows first repeatedwaitFAIL(e7ab04be3); oldFAIL log/result
remain unchanged. Wrapper caches only consumed _SessionReaderFailure class,args,
cause, not all RuntimeErrors; repeatedwait raises a newtypedexception fromsamecause.
Cache activates after FIFOeventdelivery, not onreaderEOFbeforequeuedready/terminal.
Singleconsumer only; concurrency/genericfactory/protocolshape notqualified.

Fixedsourcearchive host/guestSHA both
27aa4d8e5c236afb3dca206f0540ff85082496f2c988ec927cc536a1e3ab999c.
OwnprivateVM/frozenimage sameconstructionprovenance asCONSTRUCTION_RESULT.
Containerf02-persistent-green-v1, configurednetnone/UID501/CPU1/1GiB/swap0/
pids128/read-only/capdropALL/tmpfs128MiB; notcgroupsampledclaim.
23:05:13.911707987–23:05:14.723507624Z exit0/noOOM.
Commandpython3 -B -O -W error -m unittest discover -v:6tests,0.529s,OK.
FulllogandState retainedmethods/PERSISTENT-GREEN.log; host6tests0.423sPASS.

This establishes construction behavior foractualpipeemptyEOF,readythenEOF,
terminalthenEOF,malformedJSON andsecondwaitEOF/JSON. It doesnot prove production
defaulttimeout/fullcontroller recovery/game/native release/safety/taskbenefit.
No previousnative/officialaudit/F01allocation replay. IndependentAvicenna review
inprogress; noformal successorallocation orPR/mainadoption yet.
README documents firstcandidatehistoricalboundaries, REPEATED_WAIT_FINDING its
laterFAIL; this newcandidate addresses two repeatedwaitconstructionfailures only.
