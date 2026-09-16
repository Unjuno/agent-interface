# SCM_RIGHTS post-start descriptor injection — retained result

Decision: **RETAIN_SCM_RIGHTS_INJECTION_BOUNDARY_SCOPED**.

A2 completed 12/12 first outcomes with zero measured-ID reruns. Both arms start UID/GID65534 with no authoritative DB fd, root-owned DB mode0600/private dir0700, and pathname DB access denied.

- control/stable: 3/3 owner-socket A/B token, generation2 commit.
- control/B_change: 3/3 B rev1->rev2 detected, generation remains1, zero generation event.
- inject_fd/stable: 3/3 broker transfers one authoritative descriptor post-start via SCM_RIGHTS; B is deserialized without receipt, token A-only, generation2 commit.
- inject_fd/B_change: 3/3 old B=b1 read from injected descriptor, B becomes b2/rev2, A-only token remains current and stale generation2 commits.

A1 is retained separately as INCOMPLETE_SUPERVISION_TIMEOUT (8 complete first outcomes, 4 unstarted, no aggregate, no pooling). Frozen A2 audit errors=0. Copied-evidence corruption controls reject 4/4.

Interpretation: clean startup/close-on-exec discipline is insufficient when a post-start ambient capability can transfer authoritative descriptors. Mandatory mediation must constrain descriptor-transfer channels as well as inherited FDs and pathname access.
