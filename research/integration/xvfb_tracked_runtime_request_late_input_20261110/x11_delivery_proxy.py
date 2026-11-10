#!/usr/bin/env python3
"""Private X11 TCP proxy that can hold one client's next outbound bytes.

The experiment arms a specific accepted client by its loopback source port.
The next bytes received from that client are buffered and forwarded after a
fixed monotonic delay, even if the client closes while the bytes are held.
This is a controlled user-space delivery delay, not a network emulator.
"""

import argparse
import json
from pathlib import Path
import select
import signal
import socket
import threading
import time


class DeliveryProxy:
    def __init__(self, listen_port, upstream_host, upstream_port,
                 control_path, ready_path, events_path):
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.control_path = Path(control_path)
        self.ready_path = Path(ready_path)
        self.events_path = Path(events_path)
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self.connections = {}
        self.event_lock = threading.Lock()
        self.listener = None
        self.control = None

    def record(self, event, **fields):
        row = {'event':event, 'monotonic_ns':time.monotonic_ns(), **fields}
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.event_lock, self.events_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, sort_keys=True) + '\n')
            f.flush()
        return row

    def start(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(('127.0.0.1', self.listen_port))
        self.listen_port = self.listener.getsockname()[1]
        self.listener.listen(32)
        self.listener.settimeout(0.1)

        if self.control_path.exists():
            self.control_path.unlink()
        self.control = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.control.bind(str(self.control_path))
        self.control.listen(8)
        self.control.settimeout(0.1)

        self.ready_path.write_text(json.dumps({
            'status':'ready', 'listen_host':'127.0.0.1',
            'listen_port':self.listen_port,
            'upstream_host':self.upstream_host,
            'upstream_port':self.upstream_port,
            'control_path':str(self.control_path),
        }, sort_keys=True) + '\n', encoding='utf-8')
        self.record('proxy_ready', listen_port=self.listen_port,
                    upstream_host=self.upstream_host,
                    upstream_port=self.upstream_port)

        threading.Thread(target=self._control_loop, daemon=True,
                         name='x11-proxy-control').start()
        threading.Thread(target=self._accept_loop, daemon=True,
                         name='x11-proxy-accept').start()

    def _accept_loop(self):
        while not self.stopping.is_set():
            try:
                client, peer = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                upstream = socket.create_connection(
                    (self.upstream_host, self.upstream_port), timeout=3.0)
                upstream.settimeout(None)
            except OSError as error:
                self.record('upstream_connect_failed', peer=list(peer),
                            error=repr(error))
                client.close()
                continue
            state = {'client':client, 'upstream':upstream,
                     'peer_host':peer[0], 'peer_port':peer[1],
                     'armed_delay_ms':None, 'triggered':False,
                     'closed':False}
            with self.lock:
                self.connections[peer[1]] = state
            self.record('client_connected', peer_host=peer[0], peer_port=peer[1])
            threading.Thread(target=self._forward_client, args=(state,),
                             daemon=True, name=f'x11-proxy-up-{peer[1]}').start()
            threading.Thread(target=self._forward_server, args=(state,),
                             daemon=True, name=f'x11-proxy-down-{peer[1]}').start()

    def _control_loop(self):
        while not self.stopping.is_set():
            try:
                control, _ = self.control.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_control, args=(control,),
                             daemon=True, name='x11-proxy-control-request').start()

    def _handle_control(self, control):
        with control:
            try:
                raw = bytearray()
                while b'\n' not in raw and len(raw) < 4096:
                    chunk = control.recv(1024)
                    if not chunk:
                        break
                    raw.extend(chunk)
                request = json.loads(bytes(raw).split(b'\n', 1)[0])
                peer_port = int(request['source_port'])
                delay_ms = int(request['delay_ms'])
                if not 1 <= delay_ms <= 8000:
                    raise ValueError('delay_ms must be between 1 and 8000')
                with self.lock:
                    state = self.connections.get(peer_port)
                    if (state is None or state['closed']
                            or state['armed_delay_ms'] is not None
                            or state['triggered']):
                        response = {'status':'rejected',
                                    'reason':'client_missing_or_already_armed',
                                    'source_port':peer_port}
                    else:
                        state['armed_delay_ms'] = delay_ms
                        response = {'status':'armed', 'source_port':peer_port,
                                    'delay_ms':delay_ms,
                                    'armed_monotonic_ns':time.monotonic_ns()}
                self.record('arm_request', **response)
                control.sendall(json.dumps(response, sort_keys=True).encode()
                                + b'\n')
            except BaseException as error:
                try:
                    control.sendall(json.dumps({'status':'error',
                                                'error':repr(error)}).encode()
                                    + b'\n')
                except OSError:
                    pass

    def _forward_client(self, state):
        client, upstream = state['client'], state['upstream']
        eof = False
        try:
            while not self.stopping.is_set():
                chunk = client.recv(65536)
                if not chunk:
                    eof = True
                    self.record('client_eof', peer_port=state['peer_port'])
                    break
                with self.lock:
                    delay_ms = state['armed_delay_ms']
                    if delay_ms is not None:
                        state['armed_delay_ms'] = None
                        state['triggered'] = True
                if delay_ms is None:
                    upstream.sendall(chunk)
                    continue

                held = bytearray(chunk)
                started_ns = time.monotonic_ns()
                deadline = time.monotonic() + delay_ms / 1000
                self.record('delivery_hold_started', peer_port=state['peer_port'],
                            delay_ms=delay_ms, bytes_held=len(held),
                            hold_started_ns=started_ns)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    if eof:
                        time.sleep(remaining)
                        break
                    readable, _, _ = select.select([client], [], [], remaining)
                    if not readable:
                        break
                    extra = client.recv(65536)
                    if extra:
                        held.extend(extra)
                        if len(held) > 1024 * 1024:
                            self.record('delivery_hold_limit_exceeded',
                                        peer_port=state['peer_port'],
                                        held_bytes=len(held))
                            raise ValueError('held X11 data exceeded 1 MiB')
                    else:
                        eof = True
                        self.record('client_eof_while_held',
                                    peer_port=state['peer_port'],
                                    held_bytes=len(held))
                forward_started_ns = time.monotonic_ns()
                upstream.sendall(held)
                self.record('delivery_forwarded', peer_port=state['peer_port'],
                            delay_ms=delay_ms, bytes_forwarded=len(held),
                            hold_started_ns=started_ns,
                            forward_started_ns=forward_started_ns,
                            forward_completed_ns=time.monotonic_ns(),
                            client_closed_before_forward=eof)
                if eof:
                    break
        except (OSError, ValueError) as error:
            self.record('client_to_server_error', peer_port=state['peer_port'],
                        error=repr(error))
        finally:
            try:
                upstream.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    def _forward_server(self, state):
        client, upstream = state['client'], state['upstream']
        try:
            while not self.stopping.is_set():
                chunk = upstream.recv(65536)
                if not chunk:
                    self.record('server_eof', peer_port=state['peer_port'])
                    break
                client.sendall(chunk)
        except (OSError, ValueError) as error:
            self.record('server_to_client_error', peer_port=state['peer_port'],
                        error=repr(error))
        finally:
            self._close_state(state)

    def _close_state(self, state):
        with self.lock:
            if state['closed']:
                return
            state['closed'] = True
            if self.connections.get(state['peer_port']) is state:
                self.connections.pop(state['peer_port'], None)
        for sock in (state['client'], state['upstream']):
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        self.record('client_connection_closed', peer_port=state['peer_port'])

    def run(self):
        self.start()
        while not self.stopping.wait(0.1):
            pass
        for sock in (self.listener, self.control):
            try:
                sock.close()
            except OSError:
                pass
        try:
            self.control_path.unlink()
        except FileNotFoundError:
            pass
        self.record('proxy_stopped')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen-port', type=int, required=True)
    parser.add_argument('--upstream-host', default='127.0.0.1')
    parser.add_argument('--upstream-port', type=int, required=True)
    parser.add_argument('--control-path', required=True)
    parser.add_argument('--ready-path', required=True)
    parser.add_argument('--events-path', required=True)
    args = parser.parse_args()
    proxy = DeliveryProxy(args.listen_port, args.upstream_host,
                          args.upstream_port, args.control_path,
                          args.ready_path, args.events_path)
    signal.signal(signal.SIGTERM, lambda *_: proxy.stopping.set())
    signal.signal(signal.SIGINT, lambda *_: proxy.stopping.set())
    proxy.run()


if __name__ == '__main__':
    main()
