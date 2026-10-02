import pathlib,json,subprocess,sys
p=pathlib.Path(__file__).resolve().parent;c=p/sys.argv[1];index=int(sys.argv[2]);op=sys.argv[3];req={'op':op}
if op=='activate_review':req['source_sequence']=json.loads((c/'replies/001.json').read_text())['sequence']
if op=='mint_many':
 seq=json.loads((c/'replies/002.json').read_text())['sequence']
 req.update(source_sequence=seq,references=[{'alias':'context','point':[37,165],'region_size':[16,16]},{'alias':'rectangle','point':[353,305],'region_size':[32,32]}])
q=c/f'caller-request-{index}.json';q.write_text(json.dumps(req));v=subprocess.run(['python3',str(p/'command.py'),c.name,str(index),str(q)],capture_output=True,text=True)
(c/f'helper-{index}.stdout').write_text(v.stdout);(c/f'helper-{index}.stderr').write_text(v.stderr);print('helper_exit',v.returncode);print(v.stderr)
if v.returncode:sys.exit(v.returncode)
j=json.loads((c/'replies'/f'{index:03d}.json').read_text())['reply'];print(json.dumps(j.get('method_receipt',j) if 'image_reference' not in j else j.get('method_receipt',{'image_reference':j['image_reference']})))
if 'image_reference' in j:print('IMAGE_PATH',j['image_reference']['path'])
