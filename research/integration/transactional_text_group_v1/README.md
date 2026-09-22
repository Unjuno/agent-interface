# transactional_text_group_v1

Issue #16 finite live correctness rung. Decision: `PASS_TRANSACTIONAL_GROUP_COMPENSATION_BOUNDARY_SCOPED`.

The formal allocation is consumed. **Do not rerun `run.py --mode formal` using this allocation ID.** Use the retained raw evidence and `audit.py` for read-only review.

Files published directly include the frozen source, plan/environment/freeze, result/report, safe evidence unpacker and lossless evidence parts. The evidence capsule also retains all construction attempts/failure records, all 45 formal case directories, outer exits, audits and corruption-control outputs.

Read-only review after unpacking:

```sh
python -B unpack.py /tmp/transactional-text-group-16-review
python -B /tmp/transactional-text-group-16-review/audit.py /tmp/transactional-text-group-16-review/formal/batch00
python -B /tmp/transactional-text-group-16-review/audit.py /tmp/transactional-text-group-16-review/formal/batch01
python -B /tmp/transactional-text-group-16-review/audit.py /tmp/transactional-text-group-16-review/formal/batch02
```

Do not treat a comparator failure, physical release, or primary-value restoration as task success. See `REPORT.md`.
