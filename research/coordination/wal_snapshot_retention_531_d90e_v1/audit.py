"""Independent read-only reconstruction from wire records, SQLite bytes, and WAL checksums.
No imports from actor, runner, wrapper or vendor. No GUI/experiment execution.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil,sqlite3,struct,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIELDS=['intent_id','intent_seq','from_generation','to_generation','confirmation_content_id','confirmation_revision']

def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def expected(writes):
    hi=3+writes
    return {'generation':hi+1,'retired':hi-2,'history':[
        dict(zip(FIELDS,[f'I{s:08d}',s,s,s+1,sha(f'payload-{s}'.encode()),s])) for s in (hi-1,hi)]}

def wal_info(raw):
    if len(raw)==0:return {'extent':0,'slots':0,'valid_frames':0,'last_commit':0}
    if len(raw)<32:raise ValueError('WAL_HEADER_SHORT')
    magic,version,page,seq,salt1,salt2,c1,c2=struct.unpack('>8I',raw[:32])
    if magic not in (0x377f0682,0x377f0683) or version!=3007000 or page!=4096:raise ValueError('WAL_HEADER')
    order='<' if magic==0x377f0682 else '>'
    def checksum(block,prev=(0,0)):
        words=struct.unpack(order+str(len(block)//4)+'I',block);a,b=prev
        for i in range(0,len(words),2):a=(a+words[i]+b)&0xffffffff;b=(b+words[i+1]+a)&0xffffffff
        return a,b
    if checksum(raw[:24])!=(c1,c2):raise ValueError('WAL_HEADER_CHECKSUM')
    stride=page+24
    if (len(raw)-32)%stride:raise ValueError('WAL_FRAME_LENGTH')
    valid=0;committed=0;current=(c1,c2)
    for i in range((len(raw)-32)//stride):
        f=raw[32+i*stride:32+(i+1)*stride]
        pg,sz,s1,s2,x,y=struct.unpack('>6I',f[:24])
        if (s1,s2)!=(salt1,salt2):break  # retained tail from an earlier WAL cycle
        if not pg:raise ValueError('WAL_PAGE_ZERO')
        current=checksum(f[:8]+f[24:],current)
        if current!=(x,y):raise ValueError('WAL_FRAME_CHECKSUM')
        valid+=1
        if sz:committed=valid
    return {'extent':len(raw),'slots':(len(raw)-32)//stride,'valid_frames':valid,'last_commit':committed}

def restore_view(folder):
    # WAL is part of the database: do not use immutable=1 and silently ignore it.
    with tempfile.TemporaryDirectory(prefix='d90e-audit-') as tmp:
        dbpath=Path(tmp)/'store.sqlite'
        shutil.copyfile(folder/'store.sqlite',dbpath)
        wal=folder/'store.sqlite-wal'
        if wal.exists():shutil.copyfile(wal,Path(str(dbpath)+'-wal'))
        con=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True,isolation_level=None)
        try:
            con.execute('PRAGMA query_only=ON')
            if con.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('SQLITE_INTEGRITY')
            g,r=con.execute('SELECT generation,retired FROM meta WHERE id=1').fetchone()
            h=con.execute('SELECT '+','.join(FIELDS)+' FROM history ORDER BY intent_seq').fetchall()
            return {'generation':g,'retired':r,'history':[dict(zip(FIELDS,x)) for x in h]}
        finally:con.close()

def check_rows(rows,configs,folders,filesystem=True,formal=True):
    errors=[];checks=0;summary=[]
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:errors.append(label)
    check(len(rows)==len(configs),'DENOMINATOR')
    for row,cfg,folder in zip(rows,configs,folders):
        tag=cfg['case'];mode=cfg['mode'];writes=0
        ck=lambda ok,label:check(ok,tag+':'+label)
        ck(same(row['config'],cfg),'CONFIG');ck(row['status']=='COMPLETE','COMPLETE')
        ck(same(row['init']['view'],expected(0)),'INITIAL_STATE')
        ck(row['init']['settings']=={'journal_mode':'wal','page_size':4096,'synchronous':2,
             'wal_autocheckpoint':1,'journal_size_limit':16384,'busy_timeout':0,'read_uncommitted':0},'SETTINGS')
        start=row['reader_start'];ck(start['total_changes']==0,'READONLY_START')
        ck(start['in_transaction'] is (mode!='COPY_RELEASE'),'START_TX')
        ck(same(start['retained'],None if mode=='BEGIN_ONLY' else expected(0)),'INITIAL_CAPTURE')
        ck(('BEGIN DEFERRED' in start['sql']),'BEGIN_SQL')
        ck(any(x.startswith('SELECT') for x in start['sql']) is (mode!='BEGIN_ONLY'),'FIRST_READ_EXPOSURE')
        snaps=[(row['initial_files'],0,None)]
        sizes=[];triples=[]
        ck(len(row['stages'])==len(cfg['milestones']),'STAGE_COUNT')
        for stage,target in zip(row['stages'],cfg['milestones']):
            ck(type(stage['writes_total']) is int and stage['writes_total']==target,'MILESTONE')
            writer=stage['writer'];ck(len(writer['writes'])==target-writes,'WRITE_COUNT')
            for event in writer['writes']:
                writes+=1
                exp=expected(writes)
                ck(event['status']=='APPLIED' and same(event['after'],exp),'WRITE_STATE')
                ck(same(event['request'],exp['history'][-1]),'WRITE_REQUEST')
            ck(same(writer['view'],expected(target)),'STAGE_STATE')
            sql=writer['sql'];ck(sql.count('BEGIN IMMEDIATE')==len(writer['writes']),'WRITE_TRANSACTIONS')
            ck(sql.count('COMMIT')==len(writer['writes']),'WRITE_COMMITS')
            cp=writer['checkpoint'];ck(len(cp)==3 and all(type(x) is int for x in cp),'CP_TYPES')
            ck(cp[0]==0,'PASSIVE_FIRST_ZERO')
            if mode=='HELD_TX':ck(0<=cp[2]<cp[1],'INCOMPLETE_PASSIVE')
            else:ck(cp[2]==cp[1] and cp[1]>0,'FULL_PASSIVE')
            extent=stage['snapshot']['files']['-wal']['size'];sizes.append(extent);triples.append(cp)
            if formal and mode!='HELD_TX':ck(extent<=65536,'BOUNDED_FIXTURE_EXTENT')
            snaps.append((stage['snapshot'],target,cp))
        ck(writes==cfg['milestones'][-1],'TOTAL_WRITES')
        b=row['before_release_truncate'];a=row['after_release_truncate']
        ck(b['checkpoint'][0]==(1 if mode=='HELD_TX' else 0),'PRE_RELEASE_TRUNCATE')
        ck(a['checkpoint']==[0,0,0],'POST_RELEASE_TRUNCATE')
        ck(row['reader_release']['in_transaction'] is False,'RELEASE_TX')
        peek=row['reader_peek'];ck(peek['total_changes']==0,'READONLY_PEEK')
        ck(same(peek['reported_view'],expected(writes if mode=='BEGIN_ONLY' else 0)),'REPORTED_VIEW')
        if mode=='COPY_RELEASE':ck(peek['sql']==[] and peek['in_transaction'] is False,'COPY_NO_LATER_READ')
        else:ck(any(x.startswith('SELECT') for x in peek['sql']) and peek['in_transaction'] is True,'TX_PEEK')
        prewal=row['before_release_files']['files']['-wal']['size']
        postwal=row['after_release_files']['files']['-wal']['size']
        ck(prewal==(sizes[-1] if mode=='HELD_TX' else 0),'PRE_TRUNCATE_EXTENT')
        ck(postwal==0,'POST_TRUNCATE_EXTENT')
        if mode=='HELD_TX':
            ck(all(x<y for x,y in zip(sizes,sizes[1:])),'GROWTH')
            if formal:ck(sizes[-1]>16384,'SIZE_LIMIT_NOT_HARD_CAP')
        for role,ex in row['exits'].items():
            ck(type(ex['returncode']) is int and ex['returncode']==0,'EXIT_'+role)
            ck(ex['extra_stdout']=='','EXTRA_STDOUT_'+role)
            ck(type(ex['pid']) is int and ex['pid']>0,'PID_'+role)
            if filesystem:ck((folder/ex['stderr_file']).read_bytes()==b'','STDERR_'+role)
        ck(set(row['exits'])=={'reader','writer'},'EXIT_DENOMINATOR')
        snaps.extend([(row['before_release_files'],writes,None),(row['after_release_files'],writes,None),(row['terminal_files'],writes,None)])
        for snap,n,cp in snaps:
            ck(snap['kind']=='QUIESCENT_BYTE_COPY_NOT_LIVE_BACKUP','SNAPSHOT_KIND')
            if filesystem:
                for item in snap['files'].values():
                    raw=(folder/item['file']).read_bytes()
                    ck(len(raw)==item['size'] and sha(raw)==item['sha256'],'SNAPSHOT_BYTES')
                dbfile=folder/snap['files']['db']['file']
                ck(same(restore_view(dbfile.parent),expected(n)),'INDEPENDENT_SQLITE')
                wf=snap['files'].get('-wal')
                if wf:
                    info=wal_info((folder/wf['file']).read_bytes())
                    if cp:
                        ck(info['valid_frames']==cp[1] and info['last_commit']==cp[1],'WAL_FRAME_ACCOUNTING')
        # Cross-link complete raw actor wires and global per-command journal.
        if filesystem:
            journal=[json.loads(line) for line in (folder/'JOURNAL.jsonl').read_text().splitlines()]
            ordered_roles=['writer','reader']+['writer']*len(cfg['milestones'])+['writer','reader','reader','writer','reader','writer']
            ck([x['role'] for x in journal]==ordered_roles,'GLOBAL_COMMAND_ORDER')
            replies=[row['init'],start]+[x['writer'] for x in row['stages']]+[b,peek,row['reader_release'],a]
            ck(same([x['response'] for x in journal[:-2]],replies),'REPLY_JOINS')
            for role in ['writer','reader']:
                jj=[x for x in journal if x['role']==role]
                wirein=[json.loads(x) for x in (folder/(role+'.stdin')).read_text().splitlines()]
                wireout=[json.loads(x) for x in (folder/(role+'.stdout')).read_text().splitlines()]
                ck(same(wirein,[x['request'] for x in jj]),'STDIN_'+role)
                ck(same(wireout,[x['response'] for x in jj]),'STDOUT_'+role)
                for ix,entry in enumerate(jj):
                    r=entry['response'];ck(r['case']==tag and r['role']==role,'WIRE_SCOPE')
                    ck(r['pid']==row['exits'][role]['pid'],'WIRE_PID')
                    ck(same(r['request'],entry['request']) and r['request']['id']==ix,'REQUEST_ID')
                    ck(entry['sent_ns']<=r['begin_ns']<=r['end_ns']<=entry['received_ns'],'CLOCK_ORDER')
                    ck(r['authority']=='none' and r['input_dispatched'] is False,'NO_AUTHORITY')
                    if role=='reader':ck(r['total_changes']==0,'NO_READER_WRITES')
            ck(row['started_ns']<=journal[0]['sent_ns']<=journal[-1]['received_ns']<=row['ended_ns'],'CASE_CLOCK')
        summary.append({'case':tag,'mode':mode,'rep':cfg['rep'],'writes':writes,'wal_extents':sizes,
                        'passive':triples,'pre_release_busy':b['checkpoint'][0],'post_release_bytes':postwal})
    if formal:
        for rep in [0,1]:
            arms={x['mode']:x for x in summary if x['rep']==rep}
            if len(arms)==3:
                check(arms['HELD_TX']['wal_extents'][-1]>=4*arms['COPY_RELEASE']['wal_extents'][-1],f'RATIO_r{rep}')
    return errors,checks,summary

def mutation_controls(rows,configs,folders,formal):
    cases={
      'dropped_case':lambda r:r.pop(),
      'duplicate_config':lambda r:r[1].update(config=r[0]['config']),
      'wrong_mode':lambda r:r[0]['config'].update(mode='OTHER'),
      'false_complete':lambda r:r[0].update(status='STOP'),
      'changed_state':lambda r:r[0]['stages'][0]['writer']['writes'][0]['after'].update(retired=99),
      'boolean_exit':lambda r:r[0]['exits']['reader'].update(returncode=False),
      'missing_exit':lambda r:r[0]['exits'].pop('writer'),
      'false_truncate':lambda r:next(x for x in r if x['config']['mode']=='HELD_TX')['before_release_truncate'].update(checkpoint=[0,0,0]),
      'copy_transaction_open':lambda r:next(x for x in r if x['config']['mode']=='COPY_RELEASE')['reader_peek'].update(in_transaction=True),
      'begin_fabricated_snapshot':lambda r:next(x for x in r if x['config']['mode']=='BEGIN_ONLY')['reader_start'].update(retained=expected(0)),
      'false_passive_completion':lambda r:next(x for x in r if x['config']['mode']=='HELD_TX')['stages'][0]['writer'].update(checkpoint=[0,99,99]),
      'changed_extent':lambda r:r[0]['stages'][0]['snapshot']['files']['-wal'].update(size=1),
    }
    result={}
    for name,mut in cases.items():
        cloned=copy.deepcopy(rows);old=json.dumps(cloned,sort_keys=True);mut(cloned)
        if json.dumps(cloned,sort_keys=True)==old:raise ValueError('NOOP_CONTROL:'+name)
        try:errors,_,_=check_rows(cloned,configs,folders,filesystem=True,formal=formal);rejected=bool(errors)
        except (ValueError,KeyError,IndexError,TypeError,sqlite3.Error):rejected=True
        result[name]=rejected
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--controls',action='store_true');a=ap.parse_args()
    plan=json.loads((ROOT/'PLAN.json').read_text());configs=plan['construction'] if a.construction else sum(plan['batches'],[])
    batches=[ROOT/'construction-00'] if a.construction else [ROOT/'formal-00',ROOT/'formal-01']
    errors=[];rows=[];folders=[]
    for batch in batches:
        start=json.loads((batch/'START.json').read_text());end=json.loads((batch/'END.json').read_text())
        ex=json.loads((ROOT/(batch.name+'-execution.json')).read_text())
        if type(ex['returncode']) is not int or ex['returncode']!=0 or ex['timeout'] is not False:errors.append('BATCH_EXIT')
        if not ex['started_ns']<=start['started_ns']<=end['ended_ns']<=ex['ended_ns']:errors.append('BATCH_TIME')
        if start['pid']!=end['pid'] or start['pid']!=ex['pid']:errors.append('BATCH_PID')
        if len(start['configs'])!=end['cases']:errors.append('BATCH_ROWS')
        block=[json.loads(x) for x in (batch/'ROWS.jsonl').read_text().splitlines()]
        if not same([x['config'] for x in block],start['configs']):errors.append('BATCH_ORDER')
        for r in block:
            folder=batch/r['config']['case'];folders.append(folder);rows.append(r)
            if not same(r,json.loads((folder/'ROW.json').read_text())):errors.append('RAW_JOIN')
        for stream in ['stdout','stderr']:
            if sha((ROOT/(batch.name+'.'+stream)).read_bytes())!=ex[stream+'_sha256']:errors.append('BATCH_STREAM')
    if not a.construction:
        freeze=json.loads((ROOT/'FREEZE.json').read_text())
        for f,h in freeze['files'].items():
            if sha((ROOT/f).read_bytes())!=h:errors.append('SOURCE:'+f)
    errs,checks,summary=check_rows(rows,configs,folders,formal=not a.construction);errors+=errs
    controls=mutation_controls(rows,configs,folders,not a.construction) if a.controls and not errors else {}
    if a.controls and (len(controls)!=12 or not all(controls.values())):errors.append('CONTROLS')
    result={'decision':('PASS_CONSTRUCTION_ONLY' if a.construction else 'PASS_WAL_SNAPSHOT_RETENTION_BOUNDARY_SCOPED') if not errors else 'HOLD_OR_FAIL',
            'cases':len(rows),'write_transactions':sum(x['writes'] for x in summary),'checks':checks,
            'errors':errors,'summary':summary,'controls':controls}
    print(json.dumps(result,sort_keys=True,indent=2));sys.exit(bool(errors))
if __name__=='__main__':main()
