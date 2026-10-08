import pathlib,json,sys,time
c=pathlib.Path(__file__).resolve().parent/sys.argv[1];next_index=int(sys.argv[2]);prior=int(sys.argv[3]);v=json.loads((c/'replies'/f'{prior:03d}.json').read_text())['reply']
row={'command':next_index,'reviewed_utc_ns':time.time_ns(),'image_sha256':v['image_reference']['sha256'],'decision':sys.argv[4]}
with (c/'primary-decisions.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
print(json.dumps(row))
