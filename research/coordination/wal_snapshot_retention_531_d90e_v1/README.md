# WAL snapshot retention: research evidence, local-only publication candidate
See REPORT.md and PREREG.md. Six locally frozen cases,768 accepted fixture writes,
no reruns, scoped PASS. No public Issue/PR/CI/main integration is implied by this
package. The parent of the local publication commit is an empty packaging base,
NOT the project's main. All paths are additive; check the current main before use.

Full readable source and complete raw DB/WAL/process evidence are in evidence.tar.xz.
CAPSULE.json binds every original member. To audit saved data without new trials:

```
python -B unpack.py /tmp/d90e-new-review
cd /tmp/d90e-new-review
python -B audit.py --controls
python -B test_contract.py
```

Fresh output required. The unpacker never starts the experiment. Do not rerun
consumed run.py/execute.py formal allocations. Copy-and-release preserves a
historical payload; it is not a latest-state or input-authority guarantee.
