import argparse, os, socket, struct, time
from protocol import encode_record, REG_HARD

REQ = struct.Struct('<BQ')  # opcode, regime or ignored
OP_GET = 1
OP_HARD = 2
OP_STOP = 9

def recv_exact(c,n):
    out=bytearray()
    while len(out)<n:
        b=c.recv(n-len(out))
        if not b: raise EOFError
        out.extend(b)
    return bytes(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('path');a=ap.parse_args()
    try: os.unlink(a.path)
    except FileNotFoundError: pass
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.bind(a.path);s.listen(1)
    c,_=s.accept(); seq=0
    try:
        while True:
            op,val=REQ.unpack(recv_exact(c,REQ.size))
            if op==OP_STOP: break
            seq+=1
            regime=REG_HARD if op==OP_HARD else int(val)
            published=time.perf_counter_ns()
            c.sendall(encode_record(seq,regime,published))
    finally:
        c.close();s.close()
        try: os.unlink(a.path)
        except FileNotFoundError: pass
if __name__=='__main__':main()
