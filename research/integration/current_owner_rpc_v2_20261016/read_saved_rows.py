"""Independent saved-row oracle. No runtime import, native call or socket."""
import copy
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
EXPECTED={'peer-eof','blocked-release','stale-generation','codec','duplicate-id','lease-rebind',
'duplicate-json-member','pre-send-refusal','inconsistent-close','interrupted-close','bad-ready',
'active-generation','active-explicit-cancel','active-lease-expiry','raw-close','drop','wrong-id',
'invalid-records','partial','unsupported-window','fatal-close','fatal-group-close','paired-readiness','paired-close','paired-service','extra-reply'}


def check_receipt(receipt,verified):
    if (receipt['verified'] is not verified or receipt['physical_verification_authoritative'] is not False
            or receipt['service_id']!='owned-service-v2' or receipt['display']!=':fake'):
        raise ValueError('Receipt identity/verification differs')
    if verified:
        releases=receipt['release_records']
        if not receipt['owner_thread_stopped'] or receipt['close_error'] is not None or not releases or releases[-1]['reason']!='close':
            raise ValueError('Verified receipt lacks stopped owner and close release')
        for release in releases:
            if release['verified'] is not True or any(release[k]!=[] for k in ('keys_down','buttons_down','keys_unknown','key_state_errors')):
                raise ValueError('Release is not empty/verified')


def check(data):
    if (data['tests'],data['failures'],data['errors'],data['skipped'])!=(41,0,0,0):
        raise ValueError('Suite outcome differs')
    if len(data['rows'])!=26 or {r['case'] for r in data['rows']}!=EXPECTED:
        raise ValueError('Row inventory differs')
    rows={r['case']:r for r in data['rows']}
    codec=rows['codec']
    if codec['wire']['target_process_identity']!=codec['process'] or codec['wire']['target_window_identity']!=codec['window'] or codec['cancel_sticky'] is not True:
        raise ValueError('Codec lost original binding/sticky cancellation')
    for row in data['rows']:
        for request in row.get('requests',[]):
            if request['schema']!='input-owner-rpc-v2' or request['service_id']!='owned-service-v2':
                raise ValueError('Request identity differs')
            dto=request['lease']
            if dto is not None:
                source=dto['target_process_identity']
                if len(source)!=4 or source[1]!=dto['expected_surface'] or source[3]!=dto['deadline_ns'] or dto['target_window_identity'] is not None:
                    raise ValueError('Transmitted source binding differs')
        if 'requests' in row:
            ids=[r['request_id'] for r in row['requests']]
            if ids!=list(range(1,len(ids)+1)):
                raise ValueError('Request ordering differs')
    for name in ('drop','wrong-id','invalid-records','partial'):
        row=rows[name]
        inputs=[r for r in row['requests'] if r['op']=='down']
        if len(inputs)!=1 or inputs[0]['key']!='a' or row['post_error_send_count']!=0 or row['local_close']['verified'] is not False or row['fake_down_at_unknown']!=[38] or row['fake_down_after']!=[]:
            raise ValueError('Unknown outcome did not quarantine the same client')
        check_receipt(row['server_receipts'][0],True)
        if [(e['event'],e['code']) for e in row['edges']]!=[(2,38),(3,38)]:
            raise ValueError('Unknown-case Fake X edge inventory differs')
    blocked=rows['blocked-release']
    if blocked['local_close']['verified'] is not False or blocked['fake_down_before_resume']!=[38] or blocked['fake_down_after']!=[] or blocked['server_receipts'][0]['owner_thread_stopped'] is not False:
        raise ValueError('Blocked release was promoted')
    check_receipt(blocked['server_receipts'][0],False)
    if rows['stale-generation']['fake_down_after'] or rows['stale-generation']['post_error_send_count']!=0:
        raise ValueError('Stale generation admitted')
    for name in ('duplicate-id','lease-rebind','duplicate-json-member'):
        row=rows[name]
        check_receipt(row['receipts'][0],True)
        if row['receipts'][0]['protocol_error'] is None or [e['code'] for e in row['edges'] if e['event']==2]!=[38]:
            raise ValueError('Invalid protocol reached second input')
    for name in ('inconsistent-close','interrupted-close','fatal-close','fatal-group-close'):
        if rows[name]['local_close']['verified'] is not False:
            raise ValueError('Bad/interrupted close lost uncertainty')
    if any(rows[name]['primary_interrupt_preserved'] is not True for name in ('interrupted-close','fatal-close','fatal-group-close')):
        raise ValueError('Primary interrupt suppressed')
    for name in ('active-generation','active-explicit-cancel','active-lease-expiry'):
        row=rows[name]
        if row['release']['verified'] is not True or row['release']['keys_down']!=[]:
            raise ValueError('Active owner did not release')
        if row['admission']['target_process_identity']!=row['requests'][0]['lease']['target_process_identity']:
            raise ValueError('Owner admission differs from source')
        if row['explicit_update_sent'] != (name=='active-explicit-cancel'):
            raise ValueError('Explicit/idle control distinction lost')
        check_receipt(row['server_receipts'][0],True)
    extra=rows['extra-reply']
    if len(extra['requests'])!=1 or extra['requests'][0]['op']!='down' or extra['post_error_send_count']!=0 or extra['local_close']['verified'] is not False:
        raise ValueError('Unsolicited buffered response allowed another send')
    check_receipt(extra['server_receipts'][0],True)
    for name in ('paired-readiness','paired-close','paired-service'):
        row=rows[name]
        if row['primary_preserved'] is not True or row['cleanup_preserved'] is not True or row['primary_type']!='KeyboardInterrupt' or row['cleanup_type']!='OSError':
            raise ValueError('Paired primary/cleanup error was lost')
    if rows['unsupported-window']['refused_before_send'] is not True or rows['pre-send-refusal']['invalid_attempts_sent']!=0 or rows['bad-ready']['no_client_created'] is not True:
        raise ValueError('Readiness/local refusal differs')
    check_receipt(rows['raw-close']['close'],True)
    check_receipt(rows['peer-eof']['receipts'][0],True)
    return True


def main():
    results={}
    for mode in ('normal','optimized'):
        data=json.loads((P/f'verification/{mode}.json').read_text())
        check(data)
        for name,digest in data['source_sha256_lf'].items():
            if hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=digest:
                raise ValueError('Current source pin differs: '+name)
        rejected=[]
        for name in ('missing-row','duplicate-row','lost-source','second-send','verified-local-close','verified-blocked-owner','hidden-protocol-input','lost-interrupt','lost-paired-cleanup','accepted-extra-reply'):
            mutant=copy.deepcopy(data);rows={r['case']:r for r in mutant['rows']}
            if name=='missing-row':mutant['rows'].pop()
            if name=='duplicate-row':mutant['rows'].append(copy.deepcopy(mutant['rows'][0]))
            if name=='lost-source':rows['codec']['process'][2]='c'*64
            if name=='second-send':rows['drop']['requests'].append(copy.deepcopy(rows['drop']['requests'][0]))
            if name=='verified-local-close':rows['wrong-id']['local_close']['verified']=True
            if name=='verified-blocked-owner':rows['blocked-release']['server_receipts'][0]['verified']=True
            if name=='hidden-protocol-input':rows['lease-rebind']['edges'].append(dict(event=2,code=40,down=[40]))
            if name=='lost-interrupt':rows['interrupted-close']['primary_interrupt_preserved']=False
            if name=='lost-paired-cleanup':rows['paired-service']['cleanup_preserved']=False
            if name=='accepted-extra-reply':rows['extra-reply']['post_error_send_count']=1
            try:check(mutant)
            except ValueError:rejected.append(name)
            else:raise ValueError('Altered rows accepted: '+name)
        results[mode]=dict(rows=len(data['rows']),source_pins=len(data['source_sha256_lf']),rejected_mutants=rejected)
    report=dict(status='PASS_SAVED_SOCKET_FAKE_X_ONLY',modes=results,
                limitation='Single-process socket service/owner threads; no service process, durable receipt, default caller, native or physical timing qualification')
    (P/'verification/READBACK.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
