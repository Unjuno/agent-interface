#!/usr/bin/env python3
"""Verify the GitHub-retained subset and print the cryptographic boundary for conversation-local raw evidence."""
import hashlib,json
from pathlib import Path
r=Path(__file__).resolve().parent
m=json.loads((r/'manifest.json').read_text())
for name,want in m['frozen_source_sha256'].items():
    got=hashlib.sha256((r/name).read_bytes()).hexdigest()
    assert got==want,(name,got,want)
for name in ['REPORT.md','audit_result.json','audit_controls.json','environment.json','results_summary.json']:
    assert (r/name).is_file(),name
print(json.dumps({
    'ok':True,
    'decision':m['decision'],
    'github_retained_files':len(m['github_retained_files']),
    'raw_first_results_bound':len(m['raw_first_result_bindings']),
    'full_archive_retention':m['full_archive']['retention'],
    'full_archive_bytes':m['full_archive']['bytes'],
    'full_archive_sha256':m['full_archive']['sha256']
},sort_keys=True))
