"""Read-only stdlib oracle. Imports no experiment, queue or codec module."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

MODES = ('FIFO', 'ENCODE_THEN_SELECT', 'SELECT_THEN_ENCODE')
CONDITIONS = ('SINGLE', 'CHANGE_BURST', 'UNCHANGED_BURST', 'ABA_BURST', 'TWO_STREAMS', 'CRITICAL_BURST')
CRITICAL = {'FOCUS_CHANGED', 'AUTHORITY_REVOKED', 'LEASE_EXPIRED', 'ACTION_REJECTED', 'SAFETY_VIOLATION', 'EFFECT_VERIFIED'}


def unpack(wire):
    b = bytes.fromhex(wire)
    magic, n = struct.unpack_from('!4sI', b)
    if magic != b'AIT1':
        raise ValueError('magic')
    meta = json.loads(b[8:8+n])
    decomp = zlib.decompressobj()
    data = decomp.decompress(b[8+n:])
    if not decomp.eof or decomp.unused_data or decomp.unconsumed_tail:
        raise ValueError('compression')
    return meta, data


def advance(state, key, wire):
    meta, data = unpack(wire)
    if meta['stream'] != key or meta['base'] != state['sequence'] or meta['sequence'] != state['sequence'] + 1:
        return False, state
    w, h = meta['width'], meta['height']
    channels = {'L': 1, 'RGB': 3, 'RGBA': 4}[meta['mode']]
    if meta['kind'] == 'full':
        pixels = data
    elif meta['kind'] == 'unchanged':
        if data or state['pixels'] is None:
            raise ValueError('unchanged')
        pixels = bytes.fromhex(state['pixels'])
    else:
        pixels = bytearray.fromhex(state['pixels'])
        offset, occupied = 0, set()
        for _ in range(meta['count']):
            x, y, tw, th = struct.unpack_from('!IIII', data, offset)
            offset += 16
            if not (0 < tw <= w-x and 0 < th <= h-y):
                raise ValueError('tile bounds')
            for yy in range(y, y+th):
                for xx in range(x, x+tw):
                    if (xx, yy) in occupied:
                        raise ValueError('overlap')
                    occupied.add((xx, yy))
                    q = (yy*w+xx)*channels
                    pixels[q:q+channels] = data[offset:offset+channels]
                    offset += channels
        if offset != len(data):
            raise ValueError('tile length')
    if len(pixels) != w*h*channels:
        raise ValueError('pixel length')
    return True, {'sequence': meta['sequence'], 'metadata': meta, 'pixels': bytes(pixels).hex()}


def audit_rows(rows, construction=False):
    errors, checks = [], 0
    totals = {m: collections.Counter() for m in MODES}
    paired_inputs = {}
    expected = [(c, r, m) for c in (('SINGLE', 'CHANGE_BURST', 'CRITICAL_BURST') if construction else CONDITIONS)
                for r in range(1 if construction else 2) for m in MODES]

    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            errors.append(label)

    check([(r['condition'], r['rep'], r['mode']) for r in rows] == expected, 'schedule')
    neutral = {'sequence': 0, 'metadata': None, 'pixels': None}
    for row in rows:
        rid, mode = row['id'], row['mode']
        req = json.loads(row['producer']['stdin'])
        p = json.loads(row['producer']['stdout'])
        c = json.loads(row['consumer']['stdout'])
        totals[mode]['cases'] += 1
        check(req['mode'] == mode == p['mode'], rid+':mode')
        paired = dict(req); paired.pop('mode')
        pair_key = (row['condition'], row['rep'])
        if pair_key in paired_inputs:
            check(paired == paired_inputs[pair_key], rid+':equal_source')
        else:
            paired_inputs[pair_key] = paired
        for role, out in (('producer', p), ('consumer', c)):
            x = row[role]
            check(type(x['returncode']) is int and x['returncode'] == 0 and x['timed_out'] is False and not x['stderr'], rid+':exit:'+role)
            check(type(x['pid']) is int and x['pid'] == out['pid'] and x['end_ns'] >= x['start_ns'], rid+':process:'+role)
            check(x['argv'][-1] == {'producer': 'produce', 'consumer': 'consume'}[role], rid+':role')
        check(json.loads(row['consumer']['stdin']) == {'messages': p['messages']}, rid+':pipe')
        check(p['input_authority'] is False and c['input_authority'] is False and c['task_success'] is None, rid+':authority')
        check(p['continuous_visual_coverage'] is False and p['coverage_kind'] == ('all_supplied_frames' if mode == 'FIFO' else 'selected_frames'), rid+':coverage')
        frames = {x['record']['event_id']: x for x in req['bootstrap']+req['burst'] if x['record']['kind'] == 'FRAME'}
        records = [x['record'] for x in req['burst']]
        selected, critical, stale, coalesced = [], [], [], []
        for i, r in enumerate(records):
            eid = r['event_id']
            if r['kind'] in CRITICAL:
                selected.append(eid); critical.append(eid)
            elif req['now_ns']-r['t_ns'] > req['max_age_ns']:
                stale.append(eid)
            elif any(q['kind'] not in CRITICAL and all(q[k] == r[k] for k in ('session','target','stream')) and req['now_ns']-q['t_ns'] <= req['max_age_ns'] for q in records[i+1:]):
                coalesced.append(eid)
            else:
                selected.append(eid)
        check(p['selection'] == {'delivered_ids': selected, 'critical_ids': critical, 'stale_ids': stale, 'coalesced_ids': coalesced, 'stale_count': len(stale), 'coalesced_count': len(coalesced), 'delivered_count': len(selected), 'grants_input_authority': False}, rid+':selection')
        # Check exact fixed source images independently of the fixture generator.
        w,h = (8,8) if construction else (16,12)
        base = b''.join(hashlib.sha256(('j2c8-'+str(i)).encode()).digest() for i in range((w*h+31)//32))[:w*h]
        by_stream = collections.defaultdict(list)
        for item in req['bootstrap']:
            check(item['frame'] == {'width':w,'height':h,'mode':'L','pixels':base.hex()}, rid+':bootstrap')
        for item in req['burst']:
            r = item['record']
            check(r['session'] == rid.rsplit(':', 1)[0] and r['t_ns'] == 1000000+r['seq']*1000, rid+':source_identity')
            if r['kind'] == 'FRAME':
                by_stream[r['stream']].append(item)
        check(len(by_stream) == (2 if row['condition'] == 'TWO_STREAMS' else 1), rid+':scopes')
        for items in by_stream.values():
            check(len(items) == (1 if row['condition'] == 'SINGLE' else 3), rid+':source_count')
            for i,item in enumerate(items):
                b = bytearray(base)
                if row['condition'] != 'UNCHANGED_BURST' and not (row['condition'] == 'ABA_BURST' and i == 2):
                    b[:i+1] = bytes(255-v for v in b[:i+1])
                check(item['frame'] == {'width':w,'height':h,'mode':'L','pixels':b.hex()}, rid+':source_pixels')
        boot_ids = [x['record']['event_id'] for x in req['bootstrap']]
        source_ids = [r['event_id'] for r in records]
        deliver_ids = boot_ids + (source_ids if mode == 'FIFO' else selected)
        actual_ids = [m['record']['event_id'] if m['kind']=='CRITICAL' else m['event_id'] for m in p['messages']]
        check(actual_ids == deliver_ids, rid+':delivery_order')
        encoded_ids = boot_ids + [r['event_id'] for r in records if r['kind']=='FRAME' and (mode != 'SELECT_THEN_ENCODE' or r['event_id'] in selected)]
        check([v['event_id'] for v in p['encoded']] == encoded_ids, rid+':encoding_order')
        generation_states, wire_map = {}, {}
        for packet in p['encoded']:
            eid, key = packet['event_id'], packet['scope']
            item = frames[eid]; r=item['record']
            meta,_ = unpack(packet['wire'])
            check(key == '/'.join(r[k] for k in ('session','target','stream')), rid+':scope_binding')
            check(meta['action_id']==eid and meta['observed_ns']==r['t_ns'] and meta['context']==[r[k] for k in ('session','target','stream')], rid+':metadata')
            ok,state = advance(generation_states.get(key, neutral),key,packet['wire'])
            check(ok and state['pixels']==item['frame']['pixels'], rid+':encoded_pixels')
            generation_states[key] = state
            wire_map[eid] = packet
        states, seen, refused = {}, [], 0
        for m in p['messages']:
            if m['kind']=='CRITICAL':
                continue
            check(all(m[k]==wire_map[m['event_id']][k] for k in ('event_id','scope','wire')), rid+':selected_wire')
            key=m['scope']; before=states.get(key,neutral)
            ok,after=advance(before,key,m['wire'])
            seen.append({'event_id':m['event_id'],'scope':key,'accepted':ok,
                         'error':None if ok else 'Stream gap/reorder/wrong base: start a new stream',
                         'before':before,'after':after})
            states[key]=after
            refused+=not ok
        check(c['observations']==seen and c['final']==states,rid+':decoder')
        check(c['critical']==[r for r in records if r['kind'] in CRITICAL],rid+':critical')
        expected_refusals=(2 if row['condition']=='TWO_STREAMS' else 1) if mode=='ENCODE_THEN_SELECT' and row['condition']!='SINGLE' else 0
        check(refused==expected_refusals,rid+':refusal_gate')
        for key,state in states.items():
            latest=[x for x in req['burst'] if x['record']['kind']=='FRAME' and '/'.join(x['record'][k] for k in ('session','target','stream'))==key][-1]
            if mode!='ENCODE_THEN_SELECT' or row['condition']=='SINGLE':
                check(state['pixels']==latest['frame']['pixels'] and state['metadata']['action_id']==latest['record']['event_id'],rid+':latest')
            elif row['condition'] in ('UNCHANGED_BURST','ABA_BURST'):
                check(state['pixels']==latest['frame']['pixels'] and state['metadata']['action_id']!=latest['record']['event_id'],rid+':pixel_identity_separation')
        totals[mode].update(encoded=len(p['encoded']), delivered=len(seen), refused=refused,
                            critical=len(c['critical']), coalesced=len(coalesced),
                            encoded_bytes=sum(len(bytes.fromhex(v['wire'])) for v in p['encoded']),
                            delivered_bytes=sum(len(bytes.fromhex(v['wire'])) for v in p['messages'] if v['kind']=='FRAME'))
    return {'status':'PASS' if not errors else 'FAIL', 'rows':len(rows), 'checks':checks,
            'errors':errors, 'totals':{k:dict(v) for k,v in totals.items()}}


def load(root, phase):
    paths=sorted((root/phase).glob('*/records.jsonl'),key=lambda p:int(p.parent.name))
    rows=[json.loads(line) for path in paths for line in path.read_text().splitlines()]
    for path in paths:
        end=json.loads((path.parent/'END.json').read_text())
        ex=json.loads((path.parent/'EXIT.json').read_text())
        if type(ex['returncode']) is not int or ex['returncode']!=0 or ex['timeout'] is not False or end['rows']!=len(path.read_text().splitlines()):
            raise ValueError('batch exit or count')
    if len(paths)!=(1 if phase.startswith('construction') else 6):
        raise ValueError('batch count')
    return rows


def controls(rows, construction=False):
    baseline=audit_rows(rows,construction)
    if baseline['errors']:
        raise ValueError('invalid control baseline')
    findings=[]
    for name in ('missing_row','duplicate_row','authority','coverage','exit','coalesced','pixels','critical','acceptance','metadata'):
        data=copy.deepcopy(rows)
        idx=next(i for i,r in enumerate(data) if r['condition']=='CRITICAL_BURST' and r['mode']=='SELECT_THEN_ENCODE')
        row=data[idx]
        if name=='missing_row': data.pop()
        elif name=='duplicate_row': data.append(copy.deepcopy(data[-1]))
        elif name=='exit': row['consumer']['returncode']=True
        else:
            role='producer' if name in ('authority','coverage','coalesced') else 'consumer'
            out=json.loads(row[role]['stdout'])
            if name=='authority': out['input_authority']=True
            elif name=='coverage': out['continuous_visual_coverage']=True
            elif name=='coalesced': out['selection']['coalesced_ids']=[]
            elif name=='pixels': next(iter(out['final'].values()))['pixels']='00'
            elif name=='critical': out['critical'].pop()
            elif name=='acceptance': out['observations'][-1]['accepted']=False
            elif name=='metadata': next(iter(out['final'].values()))['metadata']['action_id']='wrong'
            row[role]['stdout']=json.dumps(out)
        if data==rows: raise ValueError('no-op mutation')
        result=audit_rows(data,construction)
        findings.append({'name':name,'rejected':bool(result['errors']), 'errors':result['errors']})
    return {'baseline_pass':True,'all_rejected':all(x['rejected'] for x in findings),'controls':findings}


if __name__=='__main__':
    root=Path(sys.argv[1]); phase=sys.argv[2]
    rows=load(root,phase)
    result=controls(rows,phase.startswith('construction')) if '--controls' in sys.argv else audit_rows(rows,phase.startswith('construction'))
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
    sys.exit(0 if result.get('status')=='PASS' or result.get('all_rejected') else 1)
