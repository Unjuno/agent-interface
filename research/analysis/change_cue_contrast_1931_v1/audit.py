#!/usr/bin/env python3
# Independent audit: deliberately does not import run.py.
import argparse,csv,gzip,hashlib,json,math
from pathlib import Path

BOUND=math.sqrt(21.0)

def srgb_linear(v):
    c=v/255.0
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4

def lum(rgb): return 0.2126*srgb_linear(rgb[0])+0.7152*srgb_linear(rgb[1])+0.0722*srgb_linear(rgb[2])
def cr(a,b):
    a,b=lum(a),lum(b); hi,lo=max(a,b),min(a,b); return (hi+0.05)/(lo+0.05)

def colors_expected():
    lattice=(0,32,64,96,128,160,192,224,255)
    s={(v,v,v) for v in range(256)}
    for r in lattice:
      for g in lattice:
       for b in lattice:s.add((r,g,b))
    s.add((0,255,0)); return s

def validate(outdir):
    out=Path(outdir); result=json.loads((out/'RESULT.json').read_text())
    rb=(out/'ROWS.csv.gz').read_bytes()
    errors=[]
    if hashlib.sha256(rb).hexdigest()!=result['rows_gzip_sha256']: errors.append('rows_sha')
    expected_cases=len(colors_expected())*4*5
    if result['counts']['cases']!=expected_cases: errors.append('case_count')
    if result['counts']['rows']!=expected_cases*4: errors.append('row_count')
    seen=0; zero=0; lt3=0; adapt_bad=0; dual_bad=0; roi_bad=0; map_bad=0; padded_bad=0; clipped=0
    with gzip.open(out/'ROWS.csv.gz','rt',encoding='utf-8',newline='') as f:
      for row in csv.DictReader(f):
        seen+=1
        bg=tuple(map(int,row['bg'].split(','))); cv=float(row['contrast_value']); mode=row['mode']
        if row['roi_preserved']!='1': roi_bad+=1
        if row['mapping_ok']!='1': map_bad+=1
        if int(row['actual_cue_px'])<int(row['expected_cue_px']): clipped+=1
        if mode=='FIXED_GREEN_OUTLINE':
          exp=cr((0,255,0),bg)
          if abs(exp-cv)>5e-10: errors.append('fixed_recompute'); break
          if abs(exp-1.0)<1e-12: zero+=1
          if exp<3.0: lt3+=1
        elif mode=='ADAPTIVE_BW_OUTLINE':
          exp=max(cr((0,0,0),bg),cr((255,255,255),bg))
          if abs(exp-cv)>5e-10: errors.append('adaptive_recompute'); break
          if exp+1e-12<BOUND: adapt_bad+=1
        else:
          exp=max(cr((0,0,0),bg),cr((255,255,255),bg))
          if abs(exp-cv)>5e-10: errors.append('dual_recompute'); break
          if exp+1e-12<BOUND: dual_bad+=1
          if mode=='PADDED_DUAL_BW_OUTLINE' and int(row['actual_cue_px'])!=int(row['expected_cue_px']): padded_bad+=1
    if seen!=result['counts']['rows']: errors.append('seen_count')
    checks={"seen":seen,"fixed_zero":zero,"fixed_lt3":lt3,"adaptive_bad":adapt_bad,"dual_bad":dual_bad,
            "roi_bad":roi_bad,"mapping_bad":map_bad,"padded_bad":padded_bad,"clipped_rows":clipped}
    # Effective corruption controls on a deep copy of the result/row metadata contract.
    controls=[]
    mutations=[
      ('rows_sha',lambda r: r.__setitem__('rows_gzip_sha256','0'*64)),
      ('case_count',lambda r: r['counts'].__setitem__('cases',r['counts']['cases']+1)),
      ('row_count',lambda r: r['counts'].__setitem__('rows',r['counts']['rows']-1)),
      ('roi_fail',lambda r: r['counts'].__setitem__('roi_preserved_fail',1)),
      ('map_fail',lambda r: r['counts'].__setitem__('mapping_fail',1)),
      ('adaptive_fail',lambda r: r['counts'].__setitem__('adaptive_bound_fail',1)),
      ('dual_fail',lambda r: r['counts'].__setitem__('dual_bound_fail',1)),
      ('padded_fail',lambda r: r['counts'].__setitem__('padded_completeness_fail',1)),
      ('zero_removed',lambda r: r['counts'].__setitem__('fixed_zero_contrast',0)),
      ('clipped_removed',lambda r: r['counts'].__setitem__('clipped_rows',0)),
      ('disposition',lambda r: r.__setitem__('disposition','PASS_UNRELATED')),
    ]
    def gate(r):
      c=r['counts']
      return (r['rows_gzip_sha256']==hashlib.sha256(rb).hexdigest() and c['cases']==expected_cases and c['rows']==expected_cases*4 and
        c['roi_preserved_fail']==0 and c['mapping_fail']==0 and c['adaptive_bound_fail']==0 and c['dual_bound_fail']==0 and
        c['padded_completeness_fail']==0 and c['fixed_zero_contrast']>0 and c['fixed_lt3']>0 and c['clipped_rows']>0 and
        r['disposition']=='PASS_SOURCE_PRESERVING_CONTRAST_CUE_SCOPED')
    import copy
    for name,mut in mutations:
      rr=copy.deepcopy(result); mut(rr); controls.append({"name":name,"rejected":not gate(rr)})
    if not all(x['rejected'] for x in controls): errors.append('corruption_control')
    # Compare stored aggregates to independent reconstruction.
    mapping={
      'fixed_zero_contrast':zero,'fixed_lt3':lt3,'adaptive_bound_fail':adapt_bad,'dual_bound_fail':dual_bad,
      'roi_preserved_fail':roi_bad,'mapping_fail':map_bad,'padded_completeness_fail':padded_bad,'clipped_rows':clipped}
    for k,v in mapping.items():
      if result['counts'][k]!=v: errors.append('aggregate_'+k)
    audit={"status":"PASS_AUDIT" if not errors else "FAIL_AUDIT","errors":errors,"checks":checks,"corruption_controls":controls,
           "sqrt21":BOUND,"formal_disposition":result.get('disposition')}
    (out/'AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    return audit

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); a=ap.parse_args(); print(json.dumps(validate(a.out),sort_keys=True))
if __name__=='__main__':main()
