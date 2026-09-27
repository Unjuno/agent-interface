# Kernel-observed exec revocation — retained result

Task `COORD-PTRACE-EXEC-REVOCATION-20260917-027`, Issue #636. Publication BASE `69e5665cb30f6c49200395343450b3f829e28804`; source-first freeze HEAD `067a8052cd4eadb2188132c22cfb77f9f5ebf992`.

Decision: **`PASS_KERNEL_EXEC_REVOCATION_SCOPED`**.

Twelve fresh formal first outcomes completed once each, with zero measured-ID reruns. The helper sends only setup READY before GO; after GO it provides no lifecycle report. In all 12 rows helper and task share the same PID and the delegated alias fd survives exec.

- `no_observer/stable`: 3/3 alias usable, SCM_RIGHTS DB descriptor delivered, token `{A}`, generation2 commits.
- `no_observer/B_change`: 3/3 alias usable, B omitted from token, B rev1→rev2 after decision, stale generation2 commits (intentional unsafe negative control).
- `ptrace_exec_revoke/stable`: 3/3 `PTRACE_EVENT_EXEC=4` / SIGTRAP observed; grantor endpoint closed before ACK/`PTRACE_CONT`; alias remains present but unusable; task falls back to A/B owner receipts; generation2 commits.
- `ptrace_exec_revoke/B_change`: 3/3 same kernel exec-stop/revocation ordering; B mismatch rejects; generation remains1 with zero generation event.

The traced Python process surfaces SIGPIPE as a post-exec ptrace stop while probing the revoked socket. The frozen supervisor records that stop and suppresses its delivery, matching CPython's normal ignored-SIGPIPE behavior; every formal ptrace row recorded post-exec stop `[13]`.

Frozen independent audit passes with zero errors. Four copied-evidence corruptions are rejected 4/4.

Interpretation: for this scoped parent/same-UID Linux process topology, the kernel exec event can replace the helper's self-reported lifecycle boundary for **post-exec** grantor revocation. It does not prevent the helper from using the capability before exec and does not establish arbitrary-process ptrace authority or a production sandbox/security boundary.
