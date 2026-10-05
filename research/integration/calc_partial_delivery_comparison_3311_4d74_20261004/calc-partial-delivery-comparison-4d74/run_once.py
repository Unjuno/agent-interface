import pathlib,json,hashlib,shutil
import model_client as M
R=pathlib.Path(__file__).resolve().parent;P=M.P
if (R/'runs').exists():raise RuntimeError('refuse model experiment replay')
for n,h in P['source_hashes'].items():
 if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h:raise RuntimeError('source drift')
if hashlib.sha256(pathlib.Path(M.CLI).read_bytes()).hexdigest()!=P['cli_sha256']:raise RuntimeError('CLI drift')
E=json.loads((R/'EVIDENCE.json').read_text(encoding='utf-8'));summary=[]
for i,arm in enumerate(P['arms']):
 D=R/'runs'/str(i);(D/'guarded/images').mkdir(parents=True)
 for f in (R/'images').glob('*.png'):shutil.copyfile(f,D/'guarded/images'/f.name)
 M.P['active_arm']='explicit';M.P['delivery_success']=arm=='delivered'
 (D/'batch.DONE.json').write_text(json.dumps(dict(image=dict(image=E['final']['native']),graph=E['graph'])),encoding='utf-8')
 proposal,usage=M.ground(D,'batch',dict(image=E['initial']['native'],source_sequence=E['initial']['sequence']),{},None)
 summary.append(dict(index=i,arm=arm,proposal=proposal,summary=usage,physical_emissions=0,evidence_delivery='prerecorded actual G14, no native process launched'))
 with (R/'SUMMARY.json').open('w',encoding='utf-8') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary))
