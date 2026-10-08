import argparse,json
from checkpoint import setup_db,store
from fixture import build_cases,FINAL

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--cases',type=int,required=True);a=p.parse_args()
    c=setup_db(a.db); c.execute('BEGIN IMMEDIATE')
    counts={'cases':0,'second_overflow':0}
    for cid,m,snap in build_cases(a.seed,a.cases):
        view=m.view(FINAL); store(c,cid,m,view); counts['cases']+=1; counts['second_overflow']+=view['A']['active_overflow'] is not None
    c.commit(); c.close(); print(json.dumps(counts,sort_keys=True))
if __name__=='__main__':main()
