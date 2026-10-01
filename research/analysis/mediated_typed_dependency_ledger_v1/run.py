import argparse,itertools,json,os,pathlib,socket,subprocess,sys,tempfile,time

def cases():
 o=[];i=0
 for g,a,b,u in itertools.product((0,1),repeat=4):
  o.append({'id':f'b{i:02d}','kind':'branch','state':{'values':{'g':g,'a':a,'b':b,'u':u},'target':'A','members':[]}});i+=1
 i=0
 for t in ('A','B'):
  for A,B,u in itertools.product((0,1),repeat=3):
   o.append({'id':f'a{i:02d}','kind':'alias','state':{'values':{'A':A,'B':B,'u':u},'target':t,'members':[]}});i+=1
 i=0
 for mA,mB,vA,vB,u in itertools.product((0,1),repeat=5):
  ms=[x for x,m in [('A',mA),('B',mB)] if m]
  o.append({'id':f'q{i:02d}','kind':'query','state':{'values':{'value_A':vA,'value_B':vB,'u':u},'target':'A','members':ms}});i+=1
 o.append({'id':'neg','kind':'bogus','state':{'values':{},'target':'A','members':[]}})
 return o

def owner(sock,cp,rp):
 cs={x['id']:x for x in json.loads(pathlib.Path(cp).read_text())};allr={};cur=None;led=[]
 try:os.unlink(sock)
 except FileNotFoundError:pass
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.bind(sock);s.listen(1);c,_=s.accept();f=c.makefile('rwb')
 def send(x):f.write((json.dumps(x,separators=(',',':'))+'\n').encode());f.flush()
 while True:
  q=json.loads(f.readline());op=q.get('op')
  if op=='BEGIN':cur=cs[q['id']];led=[];send({'ok':True});continue
  if op=='END':allr[cur['id']]={'kind':cur['kind'],'ledger':led};cur=None;led=[];send({'ok':True});continue
  if op=='STOP':send({'ok':True});break
  st=cur['state']
  if op=='READ':
   k=q['resource'];led.append({'type':'READ','resource':k,'version':1});send({'ok':True,'value':st['values'][k]})
  elif op=='RESOLVE':
   t=st['target'];led.append({'type':'RESOLVE','alias':'slot','mapping_version':1,'identity':t});send({'ok':True,'identity':t})
  elif op=='QUERY':
   led.append({'type':'QUERY','scope':'S','membership_version':1});send({'ok':True,'members':st['members']})
  else:send({'ok':False,'error':'UNKNOWN_OP'})
 pathlib.Path(rp).write_text(json.dumps(allr,sort_keys=True));c.close();s.close()

def req(f,x):f.write((json.dumps(x,separators=(',',':'))+'\n').encode());f.flush();return json.loads(f.readline())
def client(sock,sp):
 sch=json.loads(pathlib.Path(sp).read_text());c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
 for _ in range(500):
  try:c.connect(sock);break
  except OSError:time.sleep(.002)
 else:raise RuntimeError('connect')
 f=c.makefile('rwb')
 for z in sch:
  req(f,{'op':'BEGIN','id':z['id']});k=z['kind']
  if k=='branch':
   g=req(f,{'op':'READ','resource':'g'})['value'];req(f,{'op':'READ','resource':'a' if g else 'b'})
  elif k=='alias':
   t=req(f,{'op':'RESOLVE','alias':'slot'})['identity'];req(f,{'op':'READ','resource':t})
  elif k=='query':
   for m in req(f,{'op':'QUERY','scope':'S'})['members']:req(f,{'op':'READ','resource':'value_'+m})
  elif k=='bogus':assert req(f,{'op':'BOGUS'})=={'ok':False,'error':'UNKNOWN_OP'}
  req(f,{'op':'END'})
 req(f,{'op':'STOP'});c.close()

def formal(out):
 root=pathlib.Path(out);root.mkdir(parents=True,exist_ok=False);cs=cases();sch=[{'id':x['id'],'kind':x['kind']} for x in cs]
 (root/'CASES.json').write_text(json.dumps(cs,indent=2));(root/'TASK_SCHEDULE.json').write_text(json.dumps(sch,indent=2))
 with tempfile.TemporaryDirectory() as td:
  cp=td+'/c';sp=td+'/s';sock=td+'/sock';rp=td+'/raw'
  pathlib.Path(cp).write_text(json.dumps(cs));pathlib.Path(sp).write_text(json.dumps(sch))
  p=subprocess.Popen([sys.executable,__file__,'--owner',sock,cp,rp]);subprocess.check_call([sys.executable,__file__,'--client',sock,sp]);assert p.wait(timeout=5)==0
  raw=json.loads(pathlib.Path(rp).read_text())
 (root/'RAW_LEDGER.json').write_text(json.dumps(raw,indent=2,sort_keys=True))
 result={'case_count':len(cs),'scientific_case_count':len(cs)-1,'client_schedule_fields':['id','kind'],'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
 (root/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

def main():
 p=argparse.ArgumentParser();p.add_argument('--owner',nargs=3);p.add_argument('--client',nargs=2);p.add_argument('--out');a=p.parse_args()
 if a.owner:owner(*a.owner)
 elif a.client:client(*a.client)
 else:formal(a.out)
if __name__=='__main__':main()
