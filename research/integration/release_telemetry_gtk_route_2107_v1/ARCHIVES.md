# Evidence archives

Raw XWDs, event traces, receipts, case rows, cleanup records, and all earlier
construction STOP bundles are preserved in two ZIP files to keep the GitHub PR
reviewable under the file-diff API limit. The locally retained expanded folders
were not deleted.

Restore the original evidence layout from this directory with PowerShell:

```powershell
Expand-Archive evidence/packed/formal01.zip -DestinationPath evidence
Expand-Archive evidence/packed/construction-history.zip -DestinationPath evidence
```

The formal archive restores `evidence/formal01/`; the construction archive
