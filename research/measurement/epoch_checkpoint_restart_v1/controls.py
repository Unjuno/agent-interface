import os,sqlite3,tempfile,json
from checkpoint import setup_db,store,restore_row,SCHEMA
from fixture import build_cases,FINAL

def main():
    n=0; d=tempfile.mkdtemp(); p=os.path.join(d,'x.db'); cid,m,snap=next(build_cases(123,1)); expected=m.view(FINAL)
    c=setup_db(p);c.execute('BEGIN IMMEDIATE');store(c,cid,m,expected);c.commit();row=c.execute('SELECT case_id,schema,payload,sha256,expected_view,current_only FROM checkpoints').fetchone();c.close()
    _,r,e,co=restore_row(row);assert r.view(FINAL)==expected;n+=1
    bad=list(row);bad[3]='0'*64
    try:restore_row(tuple(bad))
    except ValueError:n+=1
    else:raise AssertionError('digest')
    bad=list(row);bad[1]=999
    try:restore_row(tuple(bad))
    except ValueError:n+=1
    else:raise AssertionError('schema')
    bad=list(row);bad[2]=bad[2][:-5]
    try:restore_row(tuple(bad))
    except ValueError:n+=1
    else:raise AssertionError('truncated')
    q=os.path.join(d,'uncommitted.db');c=setup_db(q);c.execute('BEGIN IMMEDIATE');store(c,cid,m,expected);c.close();c=sqlite3.connect(q);assert c.execute('SELECT count(*) FROM checkpoints').fetchone()[0]==0;c.close();n+=1
    current=json.loads(row[5]); ca=current['sessions']['A']; assert expected['A']['historical_gaps'] and ca['latest_seq']==expected['A']['latest_seq'] and 'historical_gaps' not in ca and 'epoch' not in ca and 'active_overflow' not in ca;n+=1
    print({'controls_passed':n})
if __name__=='__main__':main()
