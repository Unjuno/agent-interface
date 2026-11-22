# R14 result: queued observer binding

**Disposition: PASS for queued public observation binding.** One fresh normal and one fresh `-O` invocation both exited 0. The test occupied the event loop's only executor worker, created a supervised server while its observer was patched to a unique Fake, queued one public `interface_observe`, exited the observer patch scope, and only then released the worker. Both runs returned the exact fake observation marker, called the Fake once, and recorded zero calls to the fail-closed lower `open_session` boundary.

This establishes that binding the observation callable when `create_server` constructs its server prevents an accepted but queued worker from switching to a different module-global observer after the patch scope changes. The code change is limited to observer callable binding for that server instance. It does not establish the exact cause of R10's orphan, because R10 did not retain a worker scheduling trace. It does make the suspected mechanism deterministic and fail-closed in a controlled queue test.

No input, dispatch, task effect, recovery, native GUI, MAP01, efficiency, preview, or distribution behavior was tested. Next run the compiled caller composition with exact Fake callback counts and the lower real-observer guard, then freeze a separate reliability cohort only if that caller-path check passes.

Raw normal/optimized logs, exit codes, pretrial source hashes, and packet manifest are retained here.
