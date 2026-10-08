import argparse, os, socket, struct
from protocol import RECORD_SIZE
REQ=struct.Struct('<B'); OP_SET=1; OP_GET=2; OP_STOP=9

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
    c,_=s.accept(); current=None
    try:
        while True:
            op=REQ.unpack(recv_exact(c,REQ.size))[0]
            if op==OP_STOP: break
            if op==OP_SET:
                current=recv_exact(c,RECORD_SIZE); c.sendall(b'K')
            elif op==OP_GET:
                if current is None: raise RuntimeError('no_record')
                c.sendall(current)
            else: raise RuntimeError('opcode')
    finally:
        c.close();s.close()
        try: os.unlink(a.path)
        except FileNotFoundError: pass
if __name__=='__main__':main()
