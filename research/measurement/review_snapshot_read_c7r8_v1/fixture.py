"""Deterministic synthetic byte workload, not a live capture or task receipt."""
import hashlib, json, struct, zlib
from pathlib import Path


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def chunk(kind, data):
    return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data)&0xffffffff)


def create(root, width, height, level, condition='partial_release_failed'):
    root=Path(root); root.mkdir(parents=True, exist_ok=False)
    pixels=bytes(v for y in range(height) for x in range(width)
                 for v in ((17*x+31*y)%256, (x^y)%256, (3*x+5*y)%256))
    scan=b''.join(b'\0'+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    image=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))
    image+=chunk(b'IDAT',zlib.compress(scan,level))+chunk(b'IEND',b'')
    p=(root/'capture.png').resolve()
    p.write_bytes(image)
    native={'target':'synthetic','native_window_id':7,'frame':'window_client',
            'region':[0,0,width,height],'width':width,'height':height,
            'capture_started_ns':100,'capture_ended_ns':200,'operation_index':0,
            'sha256':hashlib.sha256(pixels).hexdigest(),
            'artifact':{'path':str(p),'mime_type':'image/png','source_raw_sha256':hashlib.sha256(pixels).hexdigest(),
                        'sha256':hashlib.sha256(image).hexdigest()}}
    report={'schema':'agent-interface/runtime-dispatch-result-v1','status':'returned',
            'synthetic_fixture':True,'result':{'status':'partial','recovery_required':True,
                'execution':{'observations':[native], 'failed_op':1,'failed_op_effect':'unknown',
                             'error':'SYNTHETIC_PARTIAL', 'releases':[{'verified':False,'keys_down':['synthetic'],'buttons_down':[]}]}}}
    if condition=='missing': p.unlink()
    elif condition=='digest_mismatch': native['artifact']['sha256']='0'*64
    elif condition=='no_observation': report['result']['execution']['observations']=[]
    elif condition!='partial_release_failed': raise ValueError(condition)
    (root/'report.json').write_bytes(canon(report))
    (root/'pixels.rgb').write_bytes(pixels)
    meta={'width':width,'height':height,'level':level,'condition':condition,'image_bytes':len(image),
          'image_sha256':hashlib.sha256(image).hexdigest(),'pixels_sha256':hashlib.sha256(pixels).hexdigest()}
    (root/'fixture.json').write_bytes(canon(meta))
    return report
