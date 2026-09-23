# ROADMAP — MUTATION-ACTOR-SUBPROCESS-PROVENANCE-20260918-001

H: fixed #1211 lineage attribution remains correct when witness records are emitted by real child processes over local IPC; temporal-nearest still produces non-self self-credit.
T: two transports (fsynced JSONL file, Unix socketpair), 1000 fresh child PIDs each; fixed semantic case schedule; independent replay oracle; source-first freeze before one formal block.
D: mismatch0, non-self self-credit0, exact-self preserved, explicit external classes exact, unknown/conflict/mismatch unattributed, no-mutation exact, temporal false-self>0, cleanup100%, authority/task-success0.
C: process provenance can still be spoofed; HUMAN/OS are injector labels, not authenticated identities.
U: local standard-library container IPC only; no GUI/network/model/task input.
STOP: one formal block, no tuning/rerun.
