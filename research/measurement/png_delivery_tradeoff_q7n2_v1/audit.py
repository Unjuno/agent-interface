"""Raw-only checks: stdlib PNG reconstruction, clocks, complete bytes and gates."""
import binascii, hashlib, json, statistics, struct, sys, zlib
from pathlib import Path


def sha(raw): return hashlib.sha256(raw).hexdigest()

def require(condition, message):
    if not condition: raise ValueError(message)


def integer(value): return type(value) is int and value >= 0


def decode_png(raw):
    require(raw[:8]==b'\x89PNG\r\n\x1a\n','PNG signature')
    offset=8; chunks=[]; compressed=bytearray(); header=None; ended=False
    while offset < len(raw):
        require(offset+12<=len(raw),'PNG chunk bounds')
        n=int.from_bytes(raw[offset:offset+4],'big'); kind=raw[offset+4:offset+8]
        payload=raw[offset+8:offset+8+n]
        require(offset+12+n<=len(raw),'PNG length')
        crc=int.from_bytes(raw[offset+8+n:offset+12+n],'big')
        require(binascii.crc32(kind+payload)&0xffffffff==crc,'PNG CRC')
        chunks.append(kind)
        if kind==b'IHDR':
            require(header is None and len(chunks)==1 and n==13,'PNG header')
            header=struct.unpack('>IIBBBBB',payload)
        elif kind==b'IDAT': compressed.extend(payload)
        elif kind==b'IEND':
            require(n==0 and offset+n+12==len(raw),'PNG ending')
            ended=True
        offset += n+12
    require(ended and header is not None,'PNG completeness')
    width,height,bits,colour,compression,filter_method,interlace=header
    require(0<width<=2048 and 0<height<=2048 and (bits,colour,compression,filter_method,interlace)==(8,2,0,0,0),'PNG layout')
    filtered=zlib.decompress(compressed)
    stride=width*3
    require(len(filtered)==height*(stride+1),'PNG decoded length')
    prior=bytearray(stride); pixels=bytearray()
    for y in range(height):
        kind=filtered[y*(stride+1)]; line=bytearray(filtered[y*(stride+1)+1:(y+1)*(stride+1)])
        require(kind<=4,'PNG filter')
        for x in range(stride):
            left=line[x-3] if x>=3 else 0; up=prior[x]; diagonal=prior[x-3] if x>=3 else 0
            if kind==1: prediction=left
            elif kind==2: prediction=up
            elif kind==3: prediction=(left+up)//2
            elif kind==4:
                p=left+up-diagonal; a=abs(p-left); b=abs(p-up); c=abs(p-diagonal)
                prediction=left if a<=b and a<=c else (up if b<=c else diagonal)
            else: prediction=0
            line[x]=(line[x]+prediction)&255
        pixels.extend(line); prior=line
    return (width,height),bytes(pixels)


def verify_row(row, png, rgb, size, identity, level, rate):
    require(row['id']==identity and type(row['level']) is int and row['level']==level and type(row['rate']) is int and row['rate']==rate,'row identity')
    require(row['emits_input'] is False and row['parent_affinity']==[0],'authority/affinity')
    require(row['ready']==json.loads(row['ready_wire']) and row['ready']=={'ready':True,'pid':row['pid'],'affinity':[1]},'readiness')
    require(type(row['pid']) is int and row['pid']>0,'PID')
    require(type(row['exit']) is int and row['exit']==0 and type(row['observed_final_exit']) is int and row['observed_final_exit']==0 and not row['stderr'],'receiver exit')
    keys=['start_ns','prepared_ns','read_file_ns','transfer_start_ns','transfer_end_ns','ack_ns','retention_end_ns']
    values=[row[k] for k in keys]
    require(all(integer(v) for v in values) and values==sorted(values),'sender clocks')
    require(integer(row['cpu_start_ns']) and integer(row['cpu_prepared_ns']) and row['cpu_prepared_ns']>=row['cpu_start_ns'],'CPU clocks')
    require(row['sink']['image_reused'] is False and integer(row['sink']['image_prepare_ns']),'sink reuse')
    require(row['start_ns']<=row['sink']['image_ready_ns']<=row['prepared_ns'] and row['sink']['image_prepare_ns']<=row['prepared_ns']-row['start_ns'],'sink clocks')
    require(integer(row['length']) and row['length']==len(png) and row['png_sha256']==sha(png) and row['rgb_sha256']==sha(rgb),'payload binding')
    require(json.loads(row['header_wire'])=={'id':identity,'length':len(png)},'header')
    ack=row['ack']
    require(ack==json.loads(row['ack_wire']),'ack wire')
    require(ack['id']==identity and ack['pid']==row['pid'] and ack['length']==len(png),'ack binding')
    require(ack['png_sha256']==sha(png) and ack['rgb_sha256']==sha(rgb) and ack['mode']=='RGB' and ack['size']==list(size) and ack['authority']=='none','ack content')
    vals=[row['start_ns']]+[ack[k] for k in ['read_start_ns','received_ns','decode_start_ns','decode_end_ns','ack_emit_ns']]+[row['ack_ns']]
    require(all(integer(v) for v in vals) and vals==sorted(vals),'receiver clocks')
    count=0; last=row['transfer_start_ns']
    for write in row['writes']:
        require(all(integer(write[k]) for k in ['offset','end','count','due_ns','before_ns','after_ns']),'write integer')
        end=min(count+4096,len(png))
        require(write['offset']==count and write['end']==end and write['count']==end-count,'write coverage')
        due=row['transfer_start_ns']+((end*1000000000+rate-1)//rate if rate else 0)
        require(write['due_ns']==due and write['before_ns']>=max(last,due) and write['after_ns']>=write['before_ns'],'pacing')
        count=end; last=write['after_ns']
    require(count==len(png) and last<=row['transfer_end_ns'],'complete transfer')
    return {'encode_ns':row['prepared_ns']-row['start_ns'],
            'decoded_ack_ns':row['ack_ns']-row['start_ns'],
            'decode_ns':ack['decode_end_ns']-ack['decode_start_ns'],'bytes':len(png)}


def audit(root):
    root=Path(root)
    freeze=json.loads((root/'FREEZE.json').read_text()); freeze_sha=sha((root/'FREEZE.json').read_bytes())
    for name, expected in freeze['files'].items(): require(sha((root/name).read_bytes())==expected,'frozen source/corpus: '+name)
    cap=json.loads((root/'corpus/CAPTURE.json').read_text())
    require(cap['server_exit']==0 and cap['socket_absent'] is True and not cap.get('error'),'capture lifecycle')
    require(cap['depth']==24 and cap['byte_order']==0 and cap['masks']==[16711680,65280,255],'capture layout')
    corpus={}
    for c in cap['captures']:
        scene=c['scene']; bgrx=(root/'corpus'/(scene+'.bgrx')).read_bytes(); rgb=(root/'corpus'/(scene+'.rgb')).read_bytes()
        require(sha(bgrx)==c['bgrx_sha256'] and sha(rgb)==c['rgb_sha256'],'corpus hashes')
        require(len(bgrx)==800*480*4 and len(rgb)==800*480*3,'corpus geometry')
        require(rgb[0::3]==bgrx[2::4] and rgb[1::3]==bgrx[1::4] and rgb[2::3]==bgrx[0::4],'X11 normalization')
        require(integer(c['start_ns']) and c['end_ns']>=c['start_ns'],'capture bracket')
        corpus[scene]=rgb
    require(set(corpus)=={'form','table','canvas'} and len(cap['captures'])==3,'corpus coverage')
    png_cache={}; measurements={}; rows_total=0
    for index in range(6):
        folder=root/'formal'/f'block-{index}'
        outer=json.loads((folder/'OUTER.json').read_text()); ending=json.loads((folder/'END.json').read_text())
        require(type(outer['returncode']) is int and outer['returncode']==0 and outer['timeout'] is False and not outer['stderr'],'outer exit')
        require(0<outer['end_ns']-outer['start_ns']<30000000000,'outer envelope')
        require(ending['index']==index and ending['rows']==6 and ending['freeze']==freeze_sha,'block end')
        rows=json.loads((folder/'ROWS.json').read_text()); require(len(rows)==6,'block denominator')
        scene=('form','table','canvas')[index//2]; rate=(0,65536)[index%2]
        schedule=[(rep,lev) for rep in range(3) for lev in ((1,6) if (index+rep)%2==0 else (6,1))]
        for row,(rep,level) in zip(rows,schedule):
            identity=f'{scene}-r{rate}-p{rep}-l{level}'; case=folder/identity
            require(row==json.loads((case/'ROW.json').read_text()),'row retention')
            require((row['scene'],row['repeat'],row['block'])==(scene,rep,index),'case schedule')
            png=(case/'producer/001.png').read_bytes(); require(png==(case/'received.png').read_bytes(),'pipe retained bytes')
            h=sha(png)
            if h not in png_cache: png_cache[h]=decode_png(png)
            require(png_cache[h]==((800,480),corpus[scene]),'decoded exact pixels')
            measures=verify_row(row,png,corpus[scene],(800,480),identity,level,rate)
            require(outer['start_ns']<=row['start_ns']<=row['retention_end_ns']<=ending['end_ns']<=outer['end_ns'],'outer chronology')
            measurements[(scene,rate,rep,level)]=measures; rows_total+=1
    summaries=[]; qualified=[]
    for scene in ('form','table','canvas'):
        encode_ratios=[]
        for rate in (0,65536):
            ratio=[measurements[scene,rate,rep,1]['decoded_ack_ns']/measurements[scene,rate,rep,6]['decoded_ack_ns'] for rep in range(3)]
            for rep in range(3): encode_ratios.append(measurements[scene,rate,rep,1]['encode_ns']/measurements[scene,rate,rep,6]['encode_ns'])
            cell={'scene':scene,'rate':rate,'paired_ack_ratios':ratio,'median_ack_ratio':statistics.median(ratio),'levels':{}}
            for level in (1,6):
                stats={}
                for key in ('encode_ns','decoded_ack_ns','decode_ns','bytes'):
                    values=[measurements[scene,rate,rep,level][key] for rep in range(3)]
                    stats[key]={'min':min(values),'median':statistics.median(values),'max':max(values)}
                cell['levels'][str(level)]=stats
            summaries.append(cell)
        slow=summaries[-1]
        qualifies=(statistics.median(encode_ratios)<=0.90 and slow['median_ack_ratio']>=1.10 and slow['levels']['1']['bytes']['min']>slow['levels']['6']['bytes']['max'])
        qualified.append({'scene':scene,'pooled_paired_median_encode_ratio':statistics.median(encode_ratios),'qualifies':qualifies})
    passed=sum(x['qualifies'] for x in qualified)>=2
    return {'integrity':'PASS','rows':rows_total,'pairs':rows_total//2,'blocks':6,'frozen_files':len(freeze['files']),
            'source_sha256':freeze_sha,'summaries':summaries,'family_gates':qualified,
            'decision':'PASS_PNG_DELIVERY_TRADEOFF_SCOPED' if passed else 'HOLD_NO_DELIVERY_RANKING_DISCRIMINATOR',
            'model_calls':0,'input_dispatched':False,'errors':[]}

if __name__=='__main__':
    try:
        result=audit(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent)
    except Exception as exc:
        print(json.dumps({'integrity':'FAIL','decision':'HOLD_EVIDENCE','errors':[str(exc)]},sort_keys=True)); raise SystemExit(1)
    print(json.dumps(result,indent=2,sort_keys=True))
