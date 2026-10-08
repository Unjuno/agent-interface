import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
rows=[
 ('positive','empty','4e8c264ddf30801ab6fd320cb503c3a100672a0f8a1502b335016ebcbd2a481a',{'field_pixels_changed':False,'field_target_present':True,'submit_target_present':False,'submission_pixels_changed':'unknown'},'d53d94f380ee0893bf459ee416f46d296d80f381b244301799d88f1210c3dbd9'),
 ('positive','filled','f4ecea32baa3b754cee972cfa389912d0b21832621f277bdb77e12d5a33f0df8',{'field_pixels_changed':True,'field_target_present':False,'submit_target_present':True,'submission_pixels_changed':'unknown'},'b2d710b5cb6778196b041e2606707e99f72c869411415a252384cb0c6cff01f5'),
 ('positive','submitted','945943813d5bf439c014df035068770f6189fdfd2bdb8e67621775713d18fa2f',{'field_pixels_changed':True,'field_target_present':False,'submit_target_present':False,'submission_pixels_changed':True},'af6c143fb60fa1079562cebb516b7934b0963a0bbcb94264bbb8a41edf335f86'),
 ('changed','empty','c8c0e48f3bdfdbae7b6e1eb0e1f4b87f5b8a77bc162c77fde8cb76f52d9a904c',{'field_pixels_changed':False,'field_target_present':True,'submit_target_present':False,'submission_pixels_changed':'unknown'},'59a5aafd8766f57844abd2ebac9e940b5f9d566f4574e16e5eb0c3a2c4de9c5b'),
 ('changed','filled','005648f9f80814d6a73f83c6f68d2d699598245a8921a1c8aa2fba9f1f0e2ead',{'field_pixels_changed':True,'field_target_present':False,'submit_target_present':False,'submission_pixels_changed':'unknown'},'e8604b0d5a3ebd996896b24bb850d83510cf21c9d9b3e6bea257d5accaddaca9'),
]
required={'empty':['field_pixels_changed','field_target_present'],'filled':['field_pixels_changed','submit_target_present'],'submitted':['submission_pixels_changed']}
def digest(image_digest,predicates):return hashlib.sha256((image_digest+json.dumps(predicates,sort_keys=True)).encode()).hexdigest()
out=[]
for case,state,image,preds,retained in rows:
    full=digest(image,preds); scoped={k:preds[k] for k in required[state]}; projected=digest(image,scoped)
    branch_only={k:preds[k] for k in required[state][:1]}; branch_digest=digest(image,branch_only)
    out.append({'case':case,'state':state,'retained_digest':retained,'recomputed_full_digest':full,'retained_reconstruction_matches':full==retained,'scoped_predicates':scoped,'projected_digest':projected,'projected_differs_from_retained':projected!=retained,'alternate_projection_digest':branch_digest,'same_world_two_projections_differ':branch_digest!=projected})
assert all(r['retained_reconstruction_matches'] for r in out)
assert all(r['projected_differs_from_retained'] for r in out)
assert all(r['same_world_two_projections_differ'] for r in out if len(required[r['state']])>=2)
summary={'rows':out,'retained_digest_reconstruction_pass':sum(r['retained_reconstruction_matches'] for r in out),'projection_changes_digest':sum(r['projected_differs_from_retained'] for r in out),'same_world_projection_only_digest_changes_comparable':sum(r['same_world_two_projections_differ'] for r in out if len(required[r['state']])>=2),'same_world_two_projection_comparable_rows':sum(len(required[r['state']])>=2 for r in out),'decision':'KEEP_CANONICAL_EVIDENCE_DIGEST_STABLE_WHILE_PROJECTING_PRESENTATION; HOLD COMPUTE PRUNING UNTIL DIGEST/PROGRESS ABI IS SEPARATED'}
(OUT/'digest_results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
