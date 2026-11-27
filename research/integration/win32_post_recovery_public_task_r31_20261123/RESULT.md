# R31 result — recovery verified; task server failed during spawn

**Disposition: `STOP_TASK_SERVER_SPAWN_IMPORT_ERROR_AFTER_RECOVERY`.** The
frozen allocation was consumed and must not be rerun.

On current main `87b5b459a56c636934947a2fc7616f26150e8b9a`, one public A action
returned UNKNOWN, release-unconfirmed, task outcome unavailable, replay denied.
One separate public orphan recovery confirmed release, neutral readback and the
2 s late-input horizon over 77 samples. The old action remained UNKNOWN. The
fixture's delayed `a` is factual only. The post-recovery exact-window foreground
probe passed, and state was `a`.

No follow-up observation or B dispatch occurred. The task-oracle server wrapper
started, but its module-level `create_server().run()` was executed again when
Windows multiprocessing spawned the recovery helper. Because the wrapper lacked
an `if __name__ == "__main__"` guard, recursive startup caused helper readiness
timeout and the MCP connection closed. The exact traceback is retained.

The durable fence is clear. Per the frozen stop rule, the fixture remains open
for diagnosis. No B task success, original-A success, matched economics,
MAP01, preview graduation, or reliability claim is made. A guarded wrapper
requires a new allocation; R31 is not retried.
