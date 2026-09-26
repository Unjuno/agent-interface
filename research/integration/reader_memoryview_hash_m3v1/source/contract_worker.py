import argparse, hashlib, importlib.util, json, os, tempfile
from pathlib import Path
from common import cursor_for, make_line, sha256_path

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def invoke(mod,path,stream='contract',cursor=None,max_records=32,max_bytes=1048576):
    try: return {'kind':'result','value':mod.read_pending(path,stream_id=stream,cursor=cursor,max_records=max_records,max_bytes=max_bytes)}
    except Exception as e: return {'kind':'error','type':type(e).__name__,'message':str(e)}

p=argparse.ArgumentParser(); p.add_argument('--arm',choices=['BASELINE','MEMORYVIEW'],required=True); a=p.parse_args()
root=Path(__file__).resolve().parent; source=root/('baseline_reader.py' if a.arm=='BASELINE' else 'candidate_reader.py'); mod=load(source,'reader_contract')
rows=[]
with tempfile.TemporaryDirectory() as td:
    d=Path(td); f=d/'s.jsonl'; lines=[make_line(i) for i in range(1,4)]; good=b''.join(lines)
    f.write_bytes(good)
    first=invoke(mod,f,max_records=2); rows.append(['page2',first])
    rows.append(['repeat_page2',invoke(mod,f,max_records=2)])
    c2=first['value']['next_cursor']; rows.append(['continue',invoke(mod,f,cursor=c2)])
    f.write_bytes(lines[0]+lines[1][:-1]); c1=cursor_for(lines[0],1,stream='contract'); rows.append(['incomplete',invoke(mod,f,cursor=c1)])
    f.write_bytes(lines[0]+b'bad\n'); rows.append(['bad_json',invoke(mod,f,cursor=c1)])
    f.write_bytes(lines[0]+b'{"event":"x","delivery_id":"delivery:3"}\n'); rows.append(['gap',invoke(mod,f,cursor=c1)])
    f.write_bytes(lines[0]+b'{"event":"x","delivery_id":"delivery:2","delivery_id":"delivery:2"}\n'); rows.append(['duplicate_key',invoke(mod,f,cursor=c1)])
    f.write_bytes(good); saved=invoke(mod,f,max_records=1)['value']['next_cursor']; changed=good.replace(b'"payload":"',b'"payload":"Y',1)[:len(good)]
    # ensure same file length by replacing one payload x with y instead of insertion
    changed=good.replace(b'xxxxxxxx',b'yxxxxxxx',1); f.write_bytes(changed); rows.append(['changed_prefix',invoke(mod,f,cursor=saved)])
    f.write_bytes(good); wrong=dict(saved,stream_id='other'); rows.append(['wrong_stream',invoke(mod,f,cursor=wrong)])
    rows.append(['bound',invoke(mod,f,max_bytes=1)])
print(json.dumps({'schema':'reader-memoryview-contract-v1','arm':a.arm,'source_sha256':sha256_path(source),'pid':os.getpid(),'rows':rows},sort_keys=True,separators=(',',':')))
