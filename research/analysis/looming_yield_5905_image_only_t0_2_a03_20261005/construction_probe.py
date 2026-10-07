import base64,gzip,json,pathlib,sys,math
p=pathlib.Path('looming-a03'); sys.path.insert(0,str(p)); import candidate
obs=json.loads(gzip.open(p/'observations.json.gz','rt',encoding='utf8').read())
# report 4-neighbour perimeter ratios against analytic circumference and raster disk radii
for seq in obs['sequences']:
 out=candidate.analyze(seq)
 print(seq['sequence_id'], round(out['features'][0]['area'],1), round(out['features'][0]['circularity'],3), round(out['features'][-1]['circularity'],3))
