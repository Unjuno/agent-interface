# ROADMAP — MUTATION-ACTOR-SQLITE-DURABLE-20260918-001

H: fixed lineage attribution remains correct when the mutation itself is durably committed by a separate process into SQLite; temporal proximity still produces false self-credit.
T: 9 case families x 80 formal cases, fresh SQLite DB per case, transactionally coupled state+event where present, parent rereads after child exit, independent oracle from durable rows, integrity_check every DB.
D: mismatch0, non-self SELF0, exact self preserved, actor classes exact, unknown/conflict/mismatch unattributed, no mutation exact, temporal false-self>0, DB integrity720/720, child cleanup complete, authority/task-success0.
C: SQLite is a controlled durable substrate; metadata can still be spoofed and this is not a real GUI actor detector.
U: standard-library local container only; HUMAN/OS are injected classes.
STOP: one formal block, reruns/replacements/tuning0.
