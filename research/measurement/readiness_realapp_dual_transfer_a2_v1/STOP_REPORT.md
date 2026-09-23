# #1259 formal transport stop

Disposition: `STOPPED_OUTER_EXECUTION_TIMEOUT`; scientific disposition **NONE**.

The fresh source-first allocation was ownership-clean and exact. Exactly one 48-case formal invocation was launched, but the outer container command timeout killed the parent formal Python process before result/exit sentinel creation. The run had created 37/48 case directories when inspected. One private Xvfb/Openbox/LibreOffice process group from the active case remained orphaned and was explicitly terminated.

No partial rows are pooled and the allocation is not rerun. A coordination/transport-only successor may preserve the exact scientific contract and replace only the launcher with a truly detached `start_new_session` supervisor.
