import os, sys

def main():
    arm, cap_fd_s, task, owner_sock, db_path = sys.argv[1:6]
    fd=int(cap_fd_s)
    helper_pid=os.getpid()
    # The single intervention: whether the capability survives the trusted-helper -> task exec boundary.
    os.set_inheritable(fd, arm == 'persistent_cap')
    os.execv(sys.executable, [sys.executable, task, owner_sock, db_path, str(fd), str(helper_pid)])
if __name__=='__main__': main()
