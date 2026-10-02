# Issue #5805 exploratory T0 — finite joint-authority contract

## H / T / D / C / U

- **H:** On fixture-authored ownership facts, requester-only admission permits some co-owned effects despite absent, conflicting, stale or forged second-owner authority. Requiring every known affected owner, or a current exact-scope delegation, blocks these cases while preserving valid private, jointly granted, delegated and mandatory release/cancel paths.
- **T:** Pure Python standard-library state enumeration on 17 fixed traces × 4 modes (`requester_only`, `all_owner_conjunction`, `scoped_delegation`, `deny_all`). Coverage includes private/shared read and write, disclosure recipient, shared-window layout, one-owner-only, joint grants, conflict/deny, stale policy generation after wait, unauthentic grant, unknown owner set, exact delegation and wrong-recipient/revoked delegation, plus release/cancel. A separate auditor checks a hand-written expected decision table and corruption controls.
- **D:** Scoped method pass only when joint/delegated modes admit zero of the frozen missing/conflicting/stale/forged/unknown-scope cases; valid exact grants and delegation progress; requester-only exposes the intended contrast; deny-all denies content effects; release/cancel remains admissible; no decision is misreported as an applied or verified effect.
- **C:** Native application/OS ACLs or human handoff may already be sufficient and would avoid a duplicate interface authorization layer. This fixture cannot decide whether a real resource is co-owned.
- **U:** All principals, affected-owner mappings, policy versions, grants, revocations, and the delegation are authored fixture facts. No real consent, signature verification, owner discovery, GUI, shared data, or real effect is used. The scenario set is finite and single-requester; no legal/product assurance follows.

## Execution boundary

This is exploratory local method evidence against an unallocated Idea Issue, not a formal repository allocation. The repository has no checkout in this task directory; the code is isolated under `scratch/`. Docker Desktop `desktop-linux` was selected but did not answer bounded `docker info` probes. No container/daemon was started or modified. Candidate and auditor run as separate local standard-library Python processes. No network, GPU, model, GUI, OS input, external service, or human participant is used.

## Acceptance

The literal auditor table expects 17 × 4 = 68 rows. `PASS_METHOD_SCOPED` is limited to the finite fixture and is not a finding that real-world unauthorized effects have been prevented.
