# Construction record

Attempt 01 used fresh multiprocessing `spawn` workers and measured evaluation timestamps from before process startup. In the supplied container, process startup dominated the intended 20/45/160/220 ms logical delays, causing false `YIELD_LATE` outcomes and defeating partial-readiness ordering. The construction audit failed and is retained under `construction01/`; it is excluded from formal evidence.

Attempt 02 changes only the execution fixture: four asyncio producers begin in one event loop and use the same logical delay/schedule/decision contract. No scientific gate is relaxed. Formal allocation is not authorized until attempt 02 passes and the resulting source/gates are published.

Preformal source review after attempt 02 found two non-scientific source inconsistencies: PLAN still described multiprocessing, and the corruption test referenced the retired `child_exits` field. Both were corrected before formal freeze. Attempt 03 reruns construction only with the corrected documentation/test source; scientific runner/auditor logic is unchanged from attempt 02.
