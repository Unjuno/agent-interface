#!/usr/bin/env python3
"""Bind the consumed fake-device result to its current-main V12 source."""
import hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
lock=json.loads((HERE/'SOURCE_LOCK.json').read_text(encoding='utf-8-sig'))
freeze=json.loads((HERE/'FREEZE.json').read_text(encoding='utf-8-sig'))
source=ROOT/lock['source_path']
snapshot=HERE/'input_owner_v12.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==lock['source_sha256']
assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==lock['source_sha256']
blob=subprocess.check_output(['git','hash-object',str(source)],cwd=ROOT,text=True).strip()
assert blob==lock['source_github_blob_sha']
assert freeze['source_sha256']==lock['source_sha256']
assert freeze['source_github_blob_sha']==lock['source_github_blob_sha']
assert freeze['base_main']==lock['experiment_base_main']
old_blob=subprocess.check_output(['git','rev-parse',f"{lock['experiment_base_main']}:{lock['source_path']}"],cwd=ROOT,text=True).strip()
new_blob=subprocess.check_output(['git','rev-parse',f"{lock['delivery_base_main']}:{lock['source_path']}"],cwd=ROOT,text=True).strip()
assert old_blob==lock['source_github_blob_sha']
assert new_blob==lock['source_github_blob_sha']
print(json.dumps({'status':'EXPERIMENT_SOURCE_BINDING_PASS','delivery_base_main':lock['delivery_base_main'],'source_sha256':lock['source_sha256'],'git_blob':blob},sort_keys=True))
