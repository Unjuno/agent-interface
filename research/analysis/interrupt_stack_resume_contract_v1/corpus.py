import itertools, json
from pathlib import Path

BOOLS=(False,True)
RESULTS=('NONE','KNOWN','UNKNOWN')

def build():
    rows=[]
    for values in itertools.product(BOOLS,BOOLS,BOOLS,BOOLS,BOOLS,RESULTS):
        interrupt_resolved,task_active,source_fresh,queue_same,target_same,pending=values
        row={
          'state_id':len(rows),
          'interrupt_resolved':interrupt_resolved,
          'task_active':task_active,
          'source_fresh':source_fresh,
          'queue_version_same':queue_same,
          'target_identity_same':target_same,
          'pending_result':pending,
        }
        rows.append(row)
    return rows

if __name__=='__main__':
    p=Path(__file__).with_name('CORPUS.json')
    p.write_text(json.dumps(build(),sort_keys=True,indent=2)+'\n')
    print(len(build()))
