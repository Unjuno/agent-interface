import json
import os
from pathlib import Path
import socket
import threading
import time
import unittest

from x11_delivery_proxy import DeliveryProxy


class X11DeliveryProxyTests(unittest.TestCase):
    def test_armed_client_bytes_forward_after_client_closes(self):
        evidence = Path(os.environ['X11_PROXY_TEST_EVIDENCE_DIR'])
        evidence.mkdir(parents=True, exist_ok=True)
        control_path = Path('/tmp/x11-proxy-test-control.sock')
        ready_path = evidence/'proxy-ready.json'
        events_path = evidence/'proxy-events.jsonl'
        received = bytearray()
        received_eof = threading.Event()
        server_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_listener.bind(('127.0.0.1', 0))
        server_listener.listen(1)
        upstream_port = server_listener.getsockname()[1]

        def receive_upstream():
            conn, _ = server_listener.accept()
            with conn:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    received.extend(chunk)
            received_eof.set()

        server_thread = threading.Thread(target=receive_upstream, daemon=True)
        server_thread.start()
        proxy = DeliveryProxy(0, '127.0.0.1', upstream_port,
                              control_path, ready_path, events_path)
        proxy_thread = threading.Thread(target=proxy.run, daemon=True)
        proxy_thread.start()
        try:
            deadline = time.monotonic()+2
            while not ready_path.exists() and time.monotonic()<deadline:
                time.sleep(0.005)
            self.assertTrue(ready_path.exists())
            ready = json.loads(ready_path.read_text(encoding='utf-8'))
            client = socket.create_connection(
                (ready['listen_host'], ready['listen_port']), timeout=2)
            client.settimeout(2)
            client.sendall(b'pre')
            deadline = time.monotonic()+2
            while bytes(received)!=b'pre' and time.monotonic()<deadline:
                time.sleep(0.005)
            self.assertEqual(bytes(received), b'pre')
            source_port = client.getsockname()[1]
            request = {'source_port':source_port, 'delay_ms':250}
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as control:
                control.settimeout(2)
                control.connect(str(control_path))
                control.sendall(json.dumps(request).encode()+b'\n')
                raw = bytearray()
                while b'\n' not in raw:
                    raw.extend(control.recv(1024))
            arm = json.loads(bytes(raw).split(b'\n',1)[0])
            self.assertEqual(arm.get('status'), 'armed', arm)
            client.sendall(b'late')
            client.shutdown(socket.SHUT_WR)
            client.close()
            self.assertTrue(received_eof.wait(3))
            self.assertEqual(bytes(received), b'prelate')
            events = [json.loads(line) for line in
                      events_path.read_text(encoding='utf-8').splitlines()]
            held = next(row for row in events
                        if row['event']=='delivery_hold_started')
            forwarded = next(row for row in events
                             if row['event']=='delivery_forwarded')
            self.assertTrue(forwarded['client_closed_before_forward'], events)
            elapsed_ms = (forwarded['forward_started_ns']
                          - held['hold_started_ns'])/1_000_000
            self.assertGreaterEqual(elapsed_ms, 240, events)
            result = {'status':'passed', 'arm':arm,
                      'received_bytes_hex':bytes(received).hex(),
                      'client_closed_before_forward':True,
                      'hold_elapsed_ms':elapsed_ms,
                      'proxy_events':events}
            (evidence/'result.json').write_text(
                json.dumps(result,indent=2,sort_keys=True)+'\n',
                encoding='utf-8')
        finally:
            proxy.stopping.set()
            proxy_thread.join(2)
            server_listener.close()
            server_thread.join(2)


if __name__ == '__main__':
    unittest.main()
