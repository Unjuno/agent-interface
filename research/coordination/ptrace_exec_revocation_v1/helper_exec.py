import os,sys

def main():
    cap=int(sys.argv[1]); task=sys.argv[2]; owner=sys.argv[3]; db=sys.argv[4]; ready=int(sys.argv[5]); go=int(sys.argv[6])
    helper_pid=os.getpid()
    alias=os.dup(cap); os.set_inheritable(alias,True); os.set_inheritable(cap,False)
    os.write(ready,b'R'); os.close(ready)
    if os.read(go,1)!=b'G': raise SystemExit('bad go')
    os.close(go)
    os.execv(sys.executable,[sys.executable,task,owner,db,str(alias),str(helper_pid)])
if __name__=='__main__':main()
