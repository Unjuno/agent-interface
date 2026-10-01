"""Raw-only reconstruction. Imports neither presenter, candidate nor worker."""
import base64,hashlib,json,statistics,struct,sys,zlib
from pathlib import Path


def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())


class Checks:
    def __init__(self):self.errors=[];self.count=0
    def __call__(self,ok,why):
        self.count+=1
        if not ok:self.errors.append(why)


def png_pixels(data):
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
    pos=8;blocks=[];payload=b'';wh=None
    while pos<len(data):
        size=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8]
        body=data[pos+8:pos+8+size];crc=data[pos+8+size:pos+12+size]
        if crc!=struct.pack('>I',zlib.crc32(kind+body)&0xffffffff):raise ValueError('PNG CRC')
        blocks.append(kind)
        if kind==b'IHDR':
            w,h,depth,mode,comp,filt,interlace=struct.unpack('>IIBBBBB',body)
            if (depth,mode,comp,filt,interlace)!=(8,2,0,0,0):raise ValueError('PNG scope')
            wh=(w,h)
        if kind==b'IDAT':payload+=body
        pos+=size+12
    if blocks!=[b'IHDR',b'IDAT',b'IEND'] or pos!=len(data) or wh is None:raise ValueError('PNG chunks')
    w,h=wh;raw=zlib.decompress(payload);row=3*w+1
    if len(raw)!=row*h or any(raw[y*row]!=0 for y in range(h)):raise ValueError('PNG scanlines')
    return w,h,b''.join(raw[y*row+1:(y+1)*row] for y in range(h))


def expected_pixels(w,h):
    channels=[]
    for y in range(h):
        for x in range(w):channels.extend(((x*17+y*31)&255,x^y,(x*3+y*5)&255))
    return bytes(v&255 for v in channels)


def output(c,blob,raw,image,condition,label):
    out=json.loads(blob);report=json.loads(raw)
    c(out.get('authority')=='none',label+':authority')
    rec=out.get('receipt',{});source=rec.get('source',{})
    c(rec.get('authority')=='none',label+':receipt authority')
    c(source.get('sha256')==sha(raw) and source.get('bytes')==len(raw),label+':report binding')
    c(source.get('raw_report')==report,label+':raw report')
    summary=out.get('outcome_summary',{})
    expected={'reported_status':'returned','error':None,'failure_phase':None,'cleanup_error':None,
              'input_release_verified':False,'failure_detail':'SYNTHETIC_PARTIAL',
              'validation_operation_index':None,'failed_operation_index':1,'failed_operation_effect':'unknown',
              'execution_status':'partial','execution_error':None,'execution_detail':None,'recovery_required':True}
    c(summary==expected,label+':summary')
    for k,v in expected.items():
        if type(v) is bool:c(type(summary.get(k)) is bool,label+':boolean '+k)
    status='image' if condition=='partial_release_failed' else ('no_observation' if condition=='no_observation' else 'needs_review')
    c(out.get('image_status')==status,label+':image status')
    if status=='image':
        item=out.get('image',{});ref=out.get('image_reference',{})
        c(item.get('type')=='image' and item.get('mimeType')=='image/png',label+':image metadata')
        c(base64.b64decode(item['data'],validate=True)==image,label+':payload')
        c(ref.get('sha256')==sha(image),label+':image digest')
        native=report['result']['execution']['observations'][0]
        keys=('target','native_window_id','frame','region','width','height','capture_started_ns','capture_ended_ns','operation_index')
        c(ref.get('recorded_capture')=={k:native[k] for k in keys},label+':capture metadata')
        c(ref.get('path')==native['artifact']['path'],label+':path')
        c(ref.get('authority')=='none',label+':image authority')
    else:c(out.get('image') is None,label+':no image')


def case(c,path,cfg,pairs,warmup):
    record=load(path/'RECORD.json');inputs=path/'inputs';raw=(inputs/'report.json').read_bytes();image=(inputs/'capture.png').read_bytes()
    c(record['condition']==cfg,'condition identity')
    c(type(record['pid']) is int and record['pid']>0,'worker pid')
    c(record['pairs']==pairs and record['warmup_pairs']==warmup,'pair configuration')
    c(record['before']==record['after'],'unchanged input declarations')
    c(record['after']=={p.name:sha(p.read_bytes()) for p in inputs.iterdir()},'unchanged input bytes')
    c(record['backend_invoked'] is False and record['model_invoked'] is False,'no runtime/model')
    c('runtime.cli_v1.api' not in record['imports'],'isolated loader')
    w,h,pixels=png_pixels(image)
    c((w,h)==(cfg['width'],cfg['height']),'PNG geometry')
    c(pixels==expected_pixels(w,h)==(inputs/'pixels.rgb').read_bytes(),'pixel recipe')
    first={}
    for policy in ('baseline','candidate'):
        b=(path/(policy+'.json')).read_bytes();first[policy]=b
        output(c,b,raw,image,'partial_release_failed',policy)
        account=record['accounting'][policy];reads=account['reads']
        c(account['output_sha256']==sha(b),'accounting output')
        c(len(reads)==(2 if policy=='baseline' else 1),'read count '+policy)
        for r in reads:
            c(type(r['bytes']) is int and r['bytes']==len(image),'read bytes '+policy)
            c(r['sha256']==sha(image),'read hash '+policy)
            c(r['path']==json.loads(raw)['result']['execution']['observations'][0]['artifact']['path'],'read path '+policy)
    c(first['baseline']==first['candidate'],'byte-identical output')
    rows=[json.loads(x) for x in (path/'samples.jsonl').read_bytes().splitlines()]
    expected=[(stage,i,p) for stage,n in [('warmup',warmup),('measured',pairs)] for i in range(n)
              for p in (['baseline','candidate'] if i%2==0 else ['candidate','baseline'])]
    c([(r['stage'],r['pair'],r['policy']) for r in rows]==expected,'sample count/order')
    end=0;times={'baseline':[],'candidate':[]};cpu={'baseline':[],'candidate':[]}
    for r in rows:
        p=r['policy'];blob=first[p]
        c(r['sha256']==sha(blob) and type(r['bytes']) is int and r['bytes']==len(blob),'sample output binding')
        ks=('wall_start_ns','wall_end_ns','cpu_start_ns','cpu_end_ns')
        c(all(type(r[k]) is int and r[k]>=0 for k in ks),'timestamp types')
        c(end<=r['wall_start_ns']<=r['wall_end_ns'],'wall order');end=r['wall_end_ns']
        c(r['cpu_start_ns']<=r['cpu_end_ns'],'CPU order')
        if r['stage']=='measured':
            times[p].append(r['wall_end_ns']-r['wall_start_ns']);cpu[p].append(r['cpu_end_ns']-r['cpu_start_ns'])
    def stats(xs):return {'median_ns':statistics.median(xs),'min_ns':min(xs),'max_ns':max(xs)}
    if all(times.values()):
        ratio=[b/a for a,b in zip(times['baseline'],times['candidate'])]
        return {'id':cfg['id'],'image_bytes':len(image),'output_bytes':len(first['baseline']),
                'wall':{p:stats(xs) for p,xs in times.items()},'cpu':{p:stats(xs) for p,xs in cpu.items()},
                'paired_wall_ratio_median':statistics.median(ratio),
                'candidate_faster_pairs':sum(b<a for a,b in zip(times['baseline'],times['candidate']))}
    return {}


def exit_record(c,parent,name,pid):
    e=load(parent/(name+'.exit.json'))
    c(type(e['returncode']) is int and e['returncode']==0,'exit '+name)
    c(e['timeout'] is False and e['pid']==pid,'exit binding '+name)
    c(type(e['started_ns']) is int and e['started_ns']<=e['ended_ns'],'exit clock '+name)
    for key in ('stdout','stderr'):
        b=(parent/(name+'.'+key)).read_bytes();c(sha(b)==e[key+'_sha256'],key+' identity '+name)
    c((parent/(name+'.stderr')).read_bytes()==b'','empty stderr '+name)
    c(load(parent/(name+'.stdout'))['pid']==pid,'stdout PID '+name)


def audit(root,construction=False):
    root=Path(root);c=Checks();summaries=[]
    try:
        if construction:
            p=root/'construction/construction'
            summaries.append(case(c,p,{'id':'construction','width':17,'height':13,'level':6},3,1))
            exit_record(c,p.parent,'construction',load(p/'RECORD.json')['pid'])
        else:
            plan=load(root/'PLAN.json');freeze=load(root/'FREEZE.json')
            for path,h in freeze['files'].items():c(sha((root/path).read_bytes())==h,'source '+path)
            for cfg in plan['conditions']:
                p=root/'formal'/cfg['id'];summaries.append(case(c,p,cfg,plan['pairs'],plan['warmup_pairs']))
                r=load(p/'RECORD.json');c(r['affinity']==[plan['affinity']],'affinity '+cfg['id'])
                exit_record(c,p.parent,cfg['id'],r['pid'])
            p=root/'formal/controls';r=load(p/'RECORD.json')
            c([v['condition'] for v in r['rows']]==plan['control_conditions'],'control denominator')
            for v in r['rows']:
                con=v['condition'];inputs=p/con
                c(v['before']==v['after']=={f.name:sha(f.read_bytes()) for f in inputs.iterdir()},'control input unchanged '+con)
                raw=(inputs/'report.json').read_bytes();img=(inputs/'capture.png').read_bytes() if (inputs/'capture.png').exists() else None
                blobs=[]
                for policy in ('baseline','candidate'):
                    b=(p/(con+'-'+policy+'.json')).read_bytes();blobs.append(b)
                    output(c,b,raw,img,con,con+' '+policy)
                c(blobs[0]==blobs[1],'control exact parity '+con)
            exit_record(c,p.parent,'controls',r['pid'])
    except (OSError,KeyError,TypeError,ValueError,struct.error,ZeroDivisionError) as e:
        c(False,'audit input error: '+type(e).__name__+': '+str(e))
    return {'verdict':('PASS_CONSTRUCTION' if construction else 'PASS_SINGLE_ACQUISITION_PRESENTATION_SCOPED') if not c.errors else 'FAIL_AUDIT',
            'checks':c.count,'errors':c.errors,'conditions':summaries,
            'performance_adoption':'NOT_ESTABLISHED','scope':'immutable-artifact historical presentation; same-author raw-only audit'}


if __name__=='__main__':
    r=audit(sys.argv[1],construction='--construction' in sys.argv)
    print(json.dumps(r,sort_keys=True,indent=2));sys.exit(bool(r['errors']))
