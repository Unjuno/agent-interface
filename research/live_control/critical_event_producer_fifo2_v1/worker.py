import argparse,sqlite3,time,sys
from model import digest,producer_offer
p=argparse.ArgumentParser(); p.add_argument('db'); p.add_argument('cap',type=int); p.add_argument('ready'); a=p.parse_args()
c=sqlite3.connect(a.db,isolation_level=None); c.execute('BEGIN IMMEDIATE')
for i in (4,5): producer_offer(c,a.cap,i,f'E{i}',digest(f'p{i}'))
c.execute('COMMIT'); open(a.ready,'w').write('committed\n'); sys.stdout.flush(); time.sleep(60)
