from pathlib import Path
import hashlib,json,re,subprocess
root=Path(__file__).resolve().parent
conditions=json.loads((root/'conditions.json').read_text(encoding='utf-8-sig'))
fail=[]
if conditions['source_revision']!=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip():fail.append('source revision changed')
for path,expected in conditions['source_sha256'].items():
 if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:fail.append(f'source hash mismatch: {path}')
for mode in ('normal','optimized'):
 text=(root/'raw'/f'{mode}.txt').read_text(encoding='utf-8-sig')
 if not re.search(r'Ran 3 tests in [0-9.]+s',text):fail.append(f'{mode}: expected three tests')
 if not re.search(r'\nOK\s*$',text):fail.append(f'{mode}: unittest did not report OK')
 if 'FAILED' in text or 'ERROR:' in text:fail.append(f'{mode}: failure marker')
result={'status':'PASS' if not fail else 'FAIL','checks':{'source_revision_and_hashes':not any('source' in f for f in fail),'normal_three_tests':not any('normal:' in f for f in fail),'optimized_three_tests':not any('optimized:' in f for f in fail)},'failures':fail,'scope':'local Windows Fake X standard-caller regression logs only'}
(root/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if not fail else 1)
