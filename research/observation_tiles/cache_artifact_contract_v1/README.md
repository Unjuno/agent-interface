# Image-cache maintenance contract (#4029)

Research-only support-envelope experiment. The original ImageArtifactSink assumes
producer-exclusive output storage. This study tests completed cooperative cache
maintenance between publications, not hostile input or concurrent mutation.
See REPORT.md for the scoped first outcome and limitations.

The nine binary parts plus PACK.json retain a lossless archive of all 157 files:
full readable frozen source and H/T/D/C/U, original vendor source, every PNG and
raw response, commands/process exits, construction history, independent audit,
and controls. Selected source and the report are also exposed directly here for
review. The public preformal FREEZE.json hash commitments are unchanged.

## Read-only reproduction (do not repeat the formal allocation)

From this directory, with a NEW output path:

```sh
python -B unpack.py /tmp/issue4029-evidence-new
cd /tmp/issue4029-evidence-new
python -B audit.py formal
python -B -m unittest -v test_contract
python -B test_contract.py --formal formal/batch0 0
python -B test_contract.py --formal formal/batch1 1
```

Unpacking and the raw-only audit require Python standard library only. Unit
checks additionally require Pillow (executed version 12.3.0); they use separate
temporary construction data, not consumed formal output. Unpack refuses an
existing destination and never executes archived source. Audit imports neither
Pillow nor the candidate. Full local validation is in PUBLICATION_CHECK.md.

Do not run execute.py/run.py against the retained paths or reuse this allocation.
No production change, Docker/OrbStack parity, model viewing, timing benefit or
completion of the global ROADMAP is claimed.
