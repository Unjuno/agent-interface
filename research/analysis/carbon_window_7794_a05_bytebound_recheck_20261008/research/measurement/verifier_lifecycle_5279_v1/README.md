# #5279 capacity-one verifier lifecycle T0

Source-first preparation for verifier-lifecycle-5279-20260929-01. Formal batches executed before this commit: zero.

The complete 10-file source/plan/environment set is losslessly retained in SOURCE.00.b64 and SOURCE.01.b64. Each part and every decoded UTF-8 file is identified by SOURCE_MANIFEST.json and FREEZE.json. worker.py and the exact inherited monitor.py are also directly readable. No model weights, runtime edits, GUI/input or deployment are included.

Restore for source review, without executing the study:

```sh
python -S -B restore.py SOURCE_MANIFEST.json /tmp/verifier-5279-source
```

Read the restored PLAN.md and PLAN.json for H/T/D/C/U, variable/unit table, proof, resource definitions and boundaries. The source set includes the separate raw-only auditor, controls and unit tests. Construction passed with its initial CPU-accounting limitation retained separately. Formal execution is finite and source-bound; do not rerun consumed batches.

Four lifecycle modes all cap concurrent workers at ONE: fresh process per job, protocol-inactive warm checkout, resident per-job reset, and resident batching of simultaneously available jobs. Primary workload: 192 job results, four repetitions; eight separate deliberate state-leak control results. No replica-scale-out, model or end-to-end computer-control benefit is claimed. Parent #5279 and the global ROADMAP remain open.
