"""Raw-only event oracle, independent of runtime and candidate execution."""
import argparse,copy,hashlib,json,re
from pathlib import Path


def tokens(path):
 if path != '/report' and not path.startswith('/report/'):raise ValueError('scope')
 result=[]
 for token in path.split('/')[1:]:
  decoded='';i=0
  while i<len(token):
   if token[i]!='~':decoded+=token[i]
   else:
    i+=1
    if i==len(token) or token[i] not in '01':raise ValueError('escape')
    decoded+= '/' if token[i]=='1' else '~'
   i+=1
  result.append(decoded)
 return result


def expected(view):
 r=copy.deepcopy(view)
 try:
  for path,number in view['event_references'].items():
   node=r;parts=tokens(path)
   for offset,token in enumerate(parts):
    if type(node) is list:
     if not re.fullmatch('0|[1-9][0-9]*',token,flags=re.ASCII):raise ValueError('index')
     key=int(token)
     if key>=len(node):raise ValueError('bounds')
    elif type(node) is dict and token in node:key=token
    else:raise ValueError('missing')
    if offset==len(parts)-1:
     if node[key]!={'event_ref':number}:raise ValueError('marker')
     node[key]=copy.deepcopy(view['events'][number])
    else:node=node[key]
 except ValueError:return {'status':'exception','exception':'ValueError'}
 r.pop('event_references');r.pop('reference_scope');r['schema']='agent-interface/receipt-view-v1'
 return {'status':'returned','output':r}


def check(raw,fixtures,source):
 errors=[];violations=[]
 if raw.get('fixture_sha256')!=hashlib.sha256(fixtures).hexdigest():errors.append('fixture hash')
 if raw.get('source_sha256')!=hashlib.sha256(source).hexdigest():errors.append('source hash')
 deck=json.loads(fixtures);rows=raw.get('rows')
 if type(rows) is not list or len(rows)!=len(deck):return {'errors':errors+['inventory'],'violations':None}
 valid=0
 for case,row in zip(deck,rows):
  want={'id':case['id'],'input_unchanged':True,**expected(case['view'])}
  valid+=want['status']=='returned'
  if json.dumps(row,sort_keys=True,allow_nan=False)!=json.dumps(want,sort_keys=True,allow_nan=False):violations.append(case['id'])
 return {'errors':errors,'violations':violations,'rows':len(rows),'valid_controls':valid}


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('fixtures',type=Path);p.add_argument('source',type=Path);p.add_argument('--require-clean',action='store_true');a=p.parse_args()
 r=check(json.loads(a.raw.read_bytes()),a.fixtures.read_bytes(),a.source.read_bytes());print(json.dumps(r,indent=2));raise SystemExit(bool(r['errors'] or (a.require_clean and r['violations'])))
