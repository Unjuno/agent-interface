import ast,hashlib,json,pathlib,shutil
P=pathlib.Path(__file__).resolve().parent
source=P/'sources/candidate';dest=P/'sources/candidate_final'
shutil.copytree(source,dest)
relative='runtime/backends/x11_v1/test_sidebutton_ledger.py'
old=(source/relative).read_bytes();new=old.rstrip(b'\n')+b'\n'
if ast.dump(ast.parse(old),include_attributes=False)!=ast.dump(ast.parse(new),include_attributes=False):raise RuntimeError('changed test AST')
(dest/relative).write_bytes(new)
(P/'EOF_NORMALIZATION.json').write_bytes((json.dumps({'path':relative,'old_bytes':len(old),'old_sha256':hashlib.sha256(old).hexdigest(),'new_bytes':len(new),'new_sha256':hashlib.sha256(new).hexdigest(),'AST_identical':True,'reason':'retained Git diff-check first failure: new blank line at EOF; remove only surplus EOF newline','prior_tested_source_retained':True},indent=2)+'\n').encode())
manifest=json.loads((P/'SOURCE_MANIFEST_REPAIRED.json').read_text(encoding='utf8'))
manifest['candidate_final']={f.relative_to(dest).as_posix():{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(dest.rglob('*')) if f.is_file()}
(P/'SOURCE_MANIFEST_FINAL.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
script=(P/'freeze.py').read_text(encoding='utf8').replace("source=P/'sources/candidate'","source=P/'sources/candidate_final'").replace("out=P/'freeze'","out=P/'freeze-final'")
(P/'freeze_final.py').write_bytes(script.encode())
print('Only excess EOF newline removed; identical test AST; original source retained.')
