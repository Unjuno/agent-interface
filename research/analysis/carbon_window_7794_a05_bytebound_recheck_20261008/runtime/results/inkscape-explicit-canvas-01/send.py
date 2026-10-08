import pathlib,json,subprocess,sys
p=pathlib.Path(__file__).resolve().parent;c=p/'canvas';index=int(sys.argv[1]);op=sys.argv[2];req={'op':op}
if op.startswith('mint'):req.update(source_sequence=1,point=[int(sys.argv[3]),int(sys.argv[4])])
q=c/f'caller-request-{index}.json';q.write_text(json.dumps(req));v=subprocess.run(['python3',str(p/'command.py'),'canvas',str(index),str(q)],capture_output=True,text=True)
(c/f'helper-{index}.stdout').write_text(v.stdout);(c/f'helper-{index}.stderr').write_text(v.stderr);print('helper_exit',v.returncode);print(v.stderr)
j=json.loads((c/'replies'/f'{index:03d}.json').read_text())['reply']
print(json.dumps(j.get('method_receipt',j) if 'image_reference' not in j else j.get('method_receipt',{'image_reference':j['image_reference']})))
if 'image_reference' in j:print('IMAGE_PATH',j['image_reference']['path'])
