# Avicenna review and exact marker identity successor

Initial independent read-only review12dc76d30/e7ab04be3: Criticalnone within
pinned singleconsumer contract. Important: type-namecache wrongly treats callback
RuntimeError subclass also named_SessionReaderFailure as permanentreaderfailure.
PERSISTENT_RESULT's "onlyconsumedreaderfailure" is therefore too strong for12dc.
Keep thathistoricalresult, narrowed bythisreview; don'tpromote6testPASS tocontract.

Actualpipe ready→terminal same-namepredicateexception reproduced poisonedcache:
7hosttests6pass/1error, queuedterminal notdelivered afterunrelatedcallbackfailure.
Successor0dfcf0722 obtains exact markerclass frompinnedreaderclosure andchecks
type(error)is marker_type. New7testhostGREEN0.488s; firstisolatedcontainer
f02-marker-identity-v1 GREEN7tests0.607s, exit0/noOOM,
23:08:48.467820291–23:08:49.323732542Z. Fulllog+State retainedmethods/MARKER-IDENTITY-GREEN.log.
Fixedhost/guestGitarchive SHA256 both
9b76b5ebb3ae07f060c0555c2596531e2ed687b99808f74b5478d89df999cf8b.
OwnVM/image/configuredlimits aspreviousF02construct; nosampledcgroupproof.

Review identified furtherlimits: testsjoinreaderbeforewait, notconcurrentarrival;
noexplicitargs/causeidentity/freshexception assertions; nofullnormalexitrace.
Cachedfailure takesprecedenceover subsequentpredicate/timeout/argumentvalidation.
Singleconsumer/pinnedsource only; noqueue reuse/restart/adoption/game/modelclaim.
Noformal/nativeallocation replay. Exactmarkerfollowupreviewrequested, pending.
Reviewer didnotindependentlyverifyinitialconstructionarchive/hostguestreceipt;
executorhashjoin retained, constructionPASS notindependentlive replication.
