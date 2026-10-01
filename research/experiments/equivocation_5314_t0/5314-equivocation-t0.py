import json

def main():
 rows=[]
 for n in (3,5,7):
  # one equivocal verifier sends COMMIT to one observer and ABORT to another;
  # honest verifiers all say COMMIT. A naive observer-local quorum can differ.
  naive_commit=naive_abort=fork_reject=0
  for observer in range(2):
   votes=['COMMIT']*(n-1)+(['COMMIT'] if observer==0 else ['ABORT'])
   naive_commit+=sum(v=='COMMIT' for v in votes)>=((n//2)+1)
   naive_abort+=sum(v=='ABORT' for v in votes)>=((n//2)+1)
   fork_reject+=int(len(set(votes))>1)
  rows.append({'verifiers':n,'observer_local_commit':naive_commit,'observer_local_abort':naive_abort,'fork_aware_reject':fork_reject})
 print(json.dumps({'experiment':'5314-equivocation-t0','rows':rows,'scope':'deterministic toy; no signatures, network ordering, identity binding, or external effect'},sort_keys=True,indent=2))
if __name__=='__main__': main()
