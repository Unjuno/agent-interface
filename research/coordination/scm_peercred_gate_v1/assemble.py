import argparse,json,pathlib
ap=argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('out'); args=ap.parse_args(); p=json.loads(pathlib.Path(args.plan).read_text()); out=pathlib.Path(args.out); rows=[]
for i in range((len(p['cases'])+p['chunk_size']-1)//p['chunk_size']): rows += json.loads((out/f'chunk-{i}.json').read_text())['rows']
(out/'aggregate.json').write_text(json.dumps({'task':p['task'],'allocation':p['allocation'],'rows':rows,'formal_reruns':0},sort_keys=True,indent=2)+'\n')
