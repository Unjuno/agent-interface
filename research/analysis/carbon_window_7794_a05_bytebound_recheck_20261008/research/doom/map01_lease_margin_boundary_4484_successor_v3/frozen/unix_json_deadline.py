"""One local JSON exchange with an absolute I/O deadline and response size bound."""
import json,math,socket,time


def exchange(path,request,*,timeout=.25,max_response_bytes=8*1024*1024):
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=35:
        raise ValueError('finite timeout 0..35 required')
    if type(max_response_bytes)is not int or not 1<=max_response_bytes<=8*1024*1024:
        raise ValueError('bounded response capacity required')
    payload=(json.dumps(request,allow_nan=False)+'\n').encode()
    if len(payload)>16384:raise ValueError('bounded request line required')
    deadline=time.monotonic()+timeout
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        def remaining():
            value=deadline-time.monotonic()
            if value<=0:raise TimeoutError('exchange deadline expired')
            connection.settimeout(value)
        remaining();connection.connect(str(path))
        remaining();connection.sendall(payload)
        chunks=bytearray()
        while True:
            remaining();part=connection.recv(min(65536,max_response_bytes-len(chunks)+1))
            if not part:raise EOFError('connection closed before complete JSON line')
            chunks.extend(part)
            if len(chunks)>max_response_bytes:raise ValueError('response exceeds byte limit')
            if b'\n' in part:
                line=bytes(chunks).split(b'\n',1)[0]
                return json.loads(line)
