import os,socket,sys

def main():
    cap_fd=int(sys.argv[1]); ctrl_fd=int(sys.argv[2]); task=sys.argv[3]; owner=sys.argv[4]; db=sys.argv[5]
    helper_pid=os.getpid()
    alias=os.dup(cap_fd); os.set_inheritable(alias,True); os.set_inheritable(cap_fd,False)
    ctrl=socket.socket(fileno=ctrl_fd); ctrl.sendall(b'BOUNDARY\n'); ack=ctrl.recv(16)
    if ack!=b'ACK\n': raise SystemExit('bad ack')
    ctrl.close()
    os.execv(sys.executable,[sys.executable,task,owner,db,str(alias),str(helper_pid)])
if __name__=='__main__': main()
