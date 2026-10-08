import argparse,json,pathlib,subprocess,sys
ap=argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('chunk',type=int); ap.add_argument('out'); args=ap.parse_args(); p=json.loads(pathlib.Path(args.plan).read_text()); size=p['chunk_size']; sel=p['cases'][args.chunk*size:(args.chunk+1)*size]; out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True); base=pathlib.Path(__file__).parent; rows=[]
for cid,arm,scenario in sel:
    cdir=out/cid; cp=subprocess.run([sys.executable,str(base/'run_case.py'),'--arm',arm,'--scenario',scenario,'--case-id',cid,'--out',str(cdir)],capture_output=True,text=True)
    if cp.returncode!=0: raise SystemExit(f'{cid} failed: {cp.stderr}')
    rows.append(json.loads((cdir/'result.json').read_text()))
(out/f'chunk-{args.chunk}.json').write_text(json.dumps({'chunk':args.chunk,'rows':rows},sort_keys=True,indent=2)+'\n')
