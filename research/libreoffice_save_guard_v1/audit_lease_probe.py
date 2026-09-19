#!/usr/bin/env python3
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());errs=[]
if r.get('allocation')!='c284-lease-probe-01':errs.append('allocation')
if r['precheck']['focus_id']!=r['calc_window_id'] or not r['precheck']['calc_alive']:errs.append('precheck')
if r['precheck']['file']!=r['post_attempt']['file']:errs.append('file mutated')
if not r['post_attempt']['calc_alive']:errs.append('calc died')
if not r['release']['verified'] or r['release']['keys_down'] or r['release']['buttons_down']:errs.append('release')
if r['classification'] not in ('LEASE_ACQUIRED','UNAVAILABLE_POST_PRECHECK'):errs.append('classification')
print(json.dumps({'pass':not errs,'errors':errs,'classification':r['classification'],'lease':r['lease']},indent=2));sys.exit(bool(errs))
