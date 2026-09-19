#!/usr/bin/env python3
import copy, hashlib, json
from pathlib import Path
ROOT=Path('/mnt/data/libreoffice_conflict_c254')
SUMMARY=ROOT/'scored-pair-02'/'SUMMARY.json'
EXPECTED={
 'pair_runner.py':'f15e57af4fa75a237e4333fee1f6a7763c2f29f979834f838534e758ff2a1a38',
 'score_any.py':'cb22bd2ab6f55c5c99a9135417b511d683fc519b193c809dedefe6ed23e6cc7a',
}
GIT_BLOBS={'backend_x11.py':'b4f8e043ce4f8929d446e038418ea0fd3655bab0','office_backend.py':'3aeca10f62fb1366bcdd5fad561509cfcc0d91ab'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(p):
 b=Path(p).read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def validate(d):
 errs=[]
 if d.get('allocation')!='c254-pair-02': errs.append('allocation')
 if d.get('order')!=['stable','replacement']: errs.append('order')
 rows={r['arm']:r for r in d.get('rows',[])}
 if set(rows)!= {'stable','replacement'}: return errs+['arms']
 s=rows['stable']; r=rows['replacement']
 for x in (s,r):
  if x['precheck']['focus_id']!=x['calc_window_id']: errs.append(x['arm']+':focus')
  if not (x['precheck']['monotonic_ns'] < x['before_save']['monotonic_ns'] < x['after_ctrl_s']['monotonic_ns'] < x['after_optional_format_confirm']['monotonic_ns'] <= x['release']['monotonic_ns']): errs.append(x['arm']+':ordering')
  if x['after_ctrl_s']['modal_names'] != ['Confirm File Format']: errs.append(x['arm']+':format_modal')
  if x.get('format_confirm_enter_sent') is not True: errs.append(x['arm']+':format_enter')
  if x['release']['verified'] is not True or x['release']['keys_down'] or x['release']['buttons_down']: errs.append(x['arm']+':release')
  if x['score']['sha256'] != x['after_optional_format_confirm']['file']['sha256']: errs.append(x['arm']+':score_hash')
 if s['classification']!='stable_saved': errs.append('stable:class')
 if s['after_optional_format_confirm']['modal_names']!=[]: errs.append('stable:post_modal')
 if s['score']['cells']!={'A1':'office','A2':'preview','A3':None,'B1':None}: errs.append('stable:cells')
 if s['precheck']['file']['sha256']!=s['before_save']['file']['sha256']: errs.append('stable:pre_file_changed')
 if s['score']['sha256']==s['precheck']['file']['sha256']: errs.append('stable:not_saved')
 ar=r.get('after_external_replace')
 if not ar: errs.append('replacement:no_replace')
 else:
  if not (r['precheck']['monotonic_ns'] < ar['monotonic_ns'] < r['before_save']['monotonic_ns']): errs.append('replacement:replace_order')
  if ar['file']['sha256'] != r['replacement_source']['sha256']: errs.append('replacement:source_hash')
  if ar['file']['ino'] == r['precheck']['file']['ino']: errs.append('replacement:inode_not_replaced')
  if r['before_save']['file']['sha256']!=ar['file']['sha256']: errs.append('replacement:pre_save_changed')
 if r['classification']!='external_preserved_with_prompt': errs.append('replacement:class')
 if r['after_optional_format_confirm']['modal_names'] != ['Document Has Been Changed by Others']: errs.append('replacement:conflict_modal')
 if r['score']['cells']!={'A1':'external','A2':'replacement','A3':'external-marker','B1':'writer'}: errs.append('replacement:cells')
 if r['score']['sha256'] != r['after_external_replace']['file']['sha256']: errs.append('replacement:not_preserved')
 return errs

d=json.loads(SUMMARY.read_text())
source_errors=[]
for f,h in EXPECTED.items():
 if sha(ROOT/f)!=h: source_errors.append(f+':sha256')
for f,h in GIT_BLOBS.items():
 if git_blob(ROOT/f)!=h: source_errors.append(f+':gitblob')
errors=source_errors+validate(d)
corruptions={}
mut=copy.deepcopy(d); mut['rows'][1]['score']['cells']['A1']='office'; corruptions['wrong_cells']=bool(validate(mut))
mut=copy.deepcopy(d); mut['rows'][1]['after_optional_format_confirm']['modal_names']=[]; corruptions['missing_conflict_modal']=bool(validate(mut))
mut=copy.deepcopy(d); mut['rows'][0]['release']['verified']=False; corruptions['bad_release']=bool(validate(mut))
mut=copy.deepcopy(d); mut['rows'][1]['before_save']['monotonic_ns']=mut['rows'][1]['precheck']['monotonic_ns']-1; corruptions['bad_order']=bool(validate(mut))
out={'schema':'agent-interface/libreoffice-save-conflict-audit-v1','allocation':'c254-pair-02','errors':errors,'pass':not errors,'corruption_rejections':corruptions,'corruption_pass':all(corruptions.values()),'source_sha256':{f:sha(ROOT/f) for f in EXPECTED},'source_git_blobs':{f:git_blob(ROOT/f) for f in GIT_BLOBS}}
(ROOT/'scored-pair-02'/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
raise SystemExit(0 if out['pass'] and out['corruption_pass'] else 1)
