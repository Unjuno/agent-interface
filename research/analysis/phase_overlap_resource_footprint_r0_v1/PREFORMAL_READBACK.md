# #1720 preformal source readback

Formal invocations at this point: **0**.

The first local SHA-256 manifest was written before remote readback. Git blob comparison showed:
- PLAN.md matched exactly;
- prove.py and audit.py did not match the local pre-upload bytes.

No formal result had been produced, so the remote GitHub bytes were reconstructed locally and made canonical before execution.

Canonical SHA-256:
- PLAN.md: 464b20566ef02c8c4d92b886a92e8980cb225e01b5c9911ffa261155ded68bec
- prove.py: aabd9add657ac72aba9f993d118243bc42b618a69d9af1ebeca6ff0310106ec8
- audit.py: 091fc8fbea980f5dad21df91108b7d6c3e9a267d9328cc481fd5ba29c1ff2c63

The original incorrect manifest commit remains in branch history as preformal provenance. No result/rerun/replacement exists before this correction.
