import cProfile,pstats,io,json,hashlib,time
from pathlib import Path
from agent_review import review_native
root=Path('results-local/native-main-use-01/run').resolve()
report=root/'reply-2.json'; before=report.read_bytes()
out=Path('results-local/native-review-profile-01');out.mkdir(exist_ok=False)
profile=cProfile.Profile(); times=[]
profile.enable()
for _ in range(8):
 t=time.perf_counter_ns(); result=review_native(report,root,compact=True); times.append((time.perf_counter_ns()-t)/1e6)
 assert result['image_status']=='image'
profile.disable()
assert report.read_bytes()==before
profile.dump_stats(str(out/'profile.pstats'))
s=io.StringIO();pstats.Stats(profile,stream=s).sort_stats('cumulative').print_stats(18)
(out/'profile.txt').write_text(s.getvalue())
(out/'result.json').write_text(json.dumps({'read_ms':times,'source_sha256':hashlib.sha256(before).hexdigest(),'image_sha256':result['image_reference']['sha256'],'scope':'profiled repeated historical read; no model, GUI or live latency claim'},indent=2))
print(s.getvalue());print(json.dumps({'read_ms':times}))
