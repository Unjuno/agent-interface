"""Independent raw-only AIT1/timing audit. Standard library; no tested imports."""
import base64
import hashlib
import json
from pathlib import Path
import statistics
import struct
import sys
import zlib

SIZES = [(129, 97), (320, 240), (641, 481)]
SCENES = ['UNCHANGED', 'LOCAL', 'SCATTER', 'DENSE_SOLID', 'DENSE_PATTERN', 'DENSE_TILE_REPEAT']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def unpack(record):
    data = zlib.decompress(base64.b64decode(record['zlib_b64'], validate=True))
    if len(data) != record['bytes'] or sha(data) != record['sha256']:
        raise ValueError('packed bytes/digest mismatch')
    return data

def decode(wire, previous=None):
    magic, length = struct.unpack('!4sI', wire[:8])
    if magic != b'AIT1':
        raise ValueError('magic')
    meta = json.loads(wire[8:8+length])
    inflater = zlib.decompressobj()
    data = inflater.decompress(wire[8+length:])
    if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError('compressed extent')
    width, height, channels = meta['width'], meta['height'], {'RGB':3, 'RGBA':4, 'L':1}[meta['mode']]
    if meta['kind'] == 'full':
        result = data
    elif meta['kind'] == 'unchanged':
        if previous is None or data:
            raise ValueError('unchanged without base')
        result = previous
    elif meta['kind'] == 'tiles':
        if previous is None:
            raise ValueError('tiles without base')
        result = bytearray(previous)
        off, seen = 0, set()
        for _ in range(meta['count']):
            x,y,w,h = struct.unpack('!IIII', data[off:off+16]); off += 16
            if not (0<w<=width and 0<h<=height and x+w<=width and y+h<=height):
                raise ValueError('tile bounds')
            for line in range(h):
                key = (y+line, x, w)
                if key in seen:
                    raise ValueError('duplicate tile')
                seen.add(key)
                start = ((y+line)*width+x)*channels
                size = w*channels
                if off+size > len(data):
                    raise ValueError('tile data extent')
                result[start:start+size] = data[off:off+size]; off += size
        if off != len(data):
            raise ValueError('tile trailing data')
        result = bytes(result)
    else:
        raise ValueError('kind')
    if len(result) != width*height*channels:
        raise ValueError('pixel extent')
    return meta, result

def changed_tiles(before, after, width, height):
    dirty = 0
    for y in range(0,height,64):
        for x in range(0,width,64):
            w,h = min(64,width-x), min(64,height-y)
            if any(before[((y+j)*width+x)*3:((y+j)*width+x+w)*3] != after[((y+j)*width+x)*3:((y+j)*width+x+w)*3] for j in range(h)):
                dirty += 1
    return dirty

def audit(root):
    root = Path(root)
    errors, summaries = [], []
    checks = 0
    def check(value, name):
        nonlocal checks
        checks += 1
        if not value:
            errors.append(name)
    try:
        freeze = json.loads((root/'FREEZE.json').read_text())
        env = json.loads((root/'ENVIRONMENT.json').read_text())
        inputs = json.loads((root/'INPUTS.json').read_text())
        for path, value in freeze['files'].items():
            check(sha((root/path).read_bytes()) == value, 'source:'+path)
        check(sorted(p.name for p in (root/'raw').glob('batch[0-9].json')) == ['batch0.json','batch1.json','batch2.json'], 'batch_denominator')
        for bi,(width,height) in enumerate(SIZES):
            raw = json.loads((root/'raw'/f'batch{bi}.json').read_text())
            process = json.loads((root/'raw'/f'batch{bi}.process.json').read_text())
            check(raw['complete'] is True and raw['batch']==bi, f'complete:{bi}')
            check(raw['freeze_sha256']==sha((root/'FREEZE.json').read_bytes()), f'freeze:{bi}')
            check(raw['affinity']==[env['selected_cpu']], f'affinity:{bi}')
            check(process['returncode']==0 and process['timeout'] is False, f'exit:{bi}')
            check(process['stderr']=='' and process['stdout']=='', f'process_output:{bi}')
            check(process['pid']==raw['pid'] and process['end_ns']>process['start_ns'], f'pid:{bi}')
            check(process['argv'][-1]==str(bi) and process['argv'][1]=='-B' and process['argv'][2].endswith('/run.py'), f'argv:{bi}')
            check(len(raw['conditions'])==6, f'conditions:{bi}')
            for si,row in enumerate(raw['conditions']):
                cid,scene = f'd8c2-{bi}-{si}',SCENES[si]
                check((row['id'],row['scene'],row['width'],row['height'])==(cid,scene,width,height), 'condition:'+cid)
                before,after = unpack(row['before']),unpack(row['after'])
                check(sha(before)==inputs[cid]['before'] and sha(after)==inputs[cid]['after'], 'fixture:'+cid)
                check(len(before)==len(after)==width*height*3, 'extent:'+cid)
                dirty = changed_tiles(before,after,width,height)
                total = ((width+63)//64)*((height+63)//64)
                check((dirty==total)==scene.startswith('DENSE'), 'density:'+cid)
                info = {}
                for arm in ('canonical','dense'):
                    first,second = unpack(row['packets'][arm]['initial']),unpack(row['packets'][arm]['update'])
                    m0,p0 = decode(first)
                    m1,p1 = decode(second,p0)
                    for m,seq,action,obs in ((m0,1,'base',100),(m1,2,'update',200)):
                        check(all(m[k]==v for k,v in dict(stream=cid,sequence=seq,base=seq-1,width=width,height=height,mode='RGB',action_id=action,observed_ns=obs,context=['synthetic']).items()), 'metadata:'+cid+arm+str(seq))
                    check(p0==before and p1==after, 'pixels:'+cid+arm)
                    check(m0['kind']=='full', 'first_full:'+cid+arm)
                    if arm=='dense' and dirty==total:
                        check(m1['kind']=='full', 'dense_full:'+cid)
                    info[arm] = dict(first=first, second=second, kind=m1['kind'])
                check(info['canonical']['first']==info['dense']['first'], 'initial_parity:'+cid)
                if dirty<total:
                    check(info['canonical']['second']==info['dense']['second'], 'nondense_parity:'+cid)
                check([x['iteration'] for x in row['samples']]==list(range(15)), 'sample_denominator:'+cid)
                check([x['iteration'] for x in row['warmups']]==[-2,-1], 'warmup_denominator:'+cid)
                wall={'canonical':[], 'dense':[]}; cpu={'canonical':[], 'dense':[]}; ratios=[]
                last_end=0
                for pair in row['warmups']+row['samples']:
                    i=pair['iteration']
                    expected=['canonical','dense'] if (i+si+bi)%2==0 else ['dense','canonical']
                    check(pair['order']==expected, 'order:'+cid+str(i))
                    for arm in pair['order']:
                        a=pair['arms'][arm]
                        check(a['wall_start']>=last_end and a['wall_end']>a['wall_start'] and a['cpu_end']>a['cpu_start'], 'clock:'+cid+str(i)+arm)
                        last_end=a['wall_end']
                        check(a['sequence']==2 and a['changed_tiles']==dirty and a['kind']==info[arm]['kind'], 'state:'+cid+str(i)+arm)
                        check(a['initial_sha256']==sha(info[arm]['first']) and a['update_sha256']==sha(info[arm]['second']), 'sample_wire:'+cid+str(i)+arm)
                        if i>=0:
                            wall[arm].append(a['wall_end']-a['wall_start']); cpu[arm].append(a['cpu_end']-a['cpu_start'])
                    if i>=0:
                        ratios.append(wall['dense'][-1]/wall['canonical'][-1])
                med=lambda xs: statistics.median(xs)
                summaries.append(dict(id=cid,scene=scene,width=width,height=height,dirty=dirty,total=total,
                    canonical_kind=info['canonical']['kind'],dense_kind=info['dense']['kind'],
                    canonical_wire=len(info['canonical']['second']),dense_wire=len(info['dense']['second']),
                    wire_ratio=len(info['dense']['second'])/len(info['canonical']['second']),paired_wall_median=med(ratios),
                    wall_ns={arm:dict(median=med(v),minimum=min(v),maximum=max(v)) for arm,v in wall.items()},
                    cpu_ns={arm:dict(median=med(v),minimum=min(v),maximum=max(v)) for arm,v in cpu.items()}))
        check(len(summaries)==18,'total_conditions')
    except Exception as exc:
        errors.append('INCOMPLETE_OR_INVALID:'+type(exc).__name__+':'+str(exc))
    gates={}
    if not errors:
        dense=[x['paired_wall_median'] for x in summaries if x['scene'].startswith('DENSE')]
        sparse=[x['paired_wall_median'] for x in summaries if x['scene'] in ('LOCAL','SCATTER')]
        gates=dict(dense_median=statistics.median(dense)<=0.80,dense_each=max(dense)<=0.90,
                   sparse_each=max(sparse)<=1.15,wire_each=max(x['wire_ratio'] for x in summaries)<=1.05)
    return dict(integrity_ok=not errors,checks=checks,errors=errors,conditions=summaries,gates=gates,
                disposition=('HOLD_INTEGRITY' if errors else 'PASS_DENSE_ROUTE_TRADEOFF_SCOPED' if all(gates.values()) else 'HOLD_DENSE_ROUTE_TRADEOFF'),
                note='Synthetic CPU update-only study; no native task, model/token or product claim.')

if __name__=='__main__':
    result=audit(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True,indent=2))
    raise SystemExit(0 if result['integrity_ok'] else 1)
