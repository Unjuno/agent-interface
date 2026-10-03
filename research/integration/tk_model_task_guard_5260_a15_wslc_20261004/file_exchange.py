"""Once-only host/container file exchange; no input or task authority.

Payloads close/fsync before the ready marker. Readers wait for a complete
marker and verify bytes before use; neither atomic-filesystem nor hostile-peer
security is claimed. The private directory is a cooperative custody boundary.
Windows host clocks are never compared with container monotonic clocks.
"""
import base64
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import time
import uuid
import sys

from host_bridge import HostBridge, sha
from model_contract import parse


def encode(value):
    return (json.dumps(value, sort_keys=True)+'\n').encode('utf-8')


def write_sealed(directory, blob, *, filename='payload.bin'):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    with (directory/filename).open('xb') as stream:
        stream.write(blob)
        stream.flush()
        os.fsync(stream.fileno())
    marker = encode({'sha256':sha(blob), 'bytes':len(blob)})
    with (directory/'ready.json').open('xb') as stream:
        stream.write(marker)
        stream.flush()
        os.fsync(stream.fileno())


def read_sealed(directory, *, filename='payload.bin'):
    directory = Path(directory)
    try:
        marker_bytes = (directory/'ready.json').read_bytes()
    except FileNotFoundError:
        return None
    # An incomplete ready-marker write is not a completed publication.
    if not marker_bytes.endswith(b'\n'):
        return None
    marker = json.loads(marker_bytes)
    if (type(marker) is not dict or set(marker) != {'sha256','bytes'}
        or type(marker['sha256']) is not str or type(marker['bytes']) is not int
        or marker['bytes'] < 0):
        raise ValueError('Invalid sealed marker')
    blob = (directory/filename).read_bytes()
    if len(blob) != marker['bytes'] or sha(blob) != marker['sha256']:
        raise ValueError('Sealed payload changed')
    return blob


class ExchangeClient:
    def __init__(self, directory, *, allocation, freeze_sha256, slots):
        self.out = Path(directory)
        self.allocation = allocation
        self.freeze_sha256 = freeze_sha256
        self.slots = set(slots)
        self.pending = {}
        self.received = set()

    def submit(self, slot, *, image, prompt):
        if slot not in self.slots or slot in self.pending:
            raise ValueError('Unknown or consumed client slot')
        request = dict(allocation=self.allocation, freeze_sha256=self.freeze_sha256,
            slot=slot, nonce=uuid.uuid4().hex,
            image_sha256=sha(image), prompt_sha256=sha(prompt))
        # Consume before publishing even if a partial write fails.
        self.pending[slot] = request
        directory = self.out/slot
        directory.mkdir(exist_ok=False)
        write_sealed(directory/'image', image, filename='payload.png')
        write_sealed(directory/'prompt', prompt)
        write_sealed(directory/'request', encode(request))
        return deepcopy(request)

    def receive(self, slot):
        if slot not in self.pending or slot in self.received:
            raise ValueError('No pending or already consumed response')
        try:
            blob = read_sealed(self.out/slot/'response')
        except Exception:
            self.received.add(slot)
            raise
        if blob is None:
            return None
        # A published response is consumed even on validation failure.
        self.received.add(slot)
        response_seen_ns = time.monotonic_ns()
        envelope = json.loads(blob)
        reply = envelope['reply']
        if reply['request'] != self.pending[slot]:
            raise ValueError('Response request/nonce mismatch')
        stdout = base64.b64decode(envelope['stdout_base64'], validate=True)
        stderr = base64.b64decode(envelope['stderr_base64'], validate=True)
        if (sha(stdout) != reply['process']['output_sha256']['stdout.bin']
            or sha(stderr) != reply['process']['output_sha256']['stderr.bin']):
            raise ValueError('Original process response mismatch')
        if reply['status'] == 'returned':
            original = parse([json.loads(line) for line in stdout.decode('utf-8').splitlines()
                              if line])
            if original != reply['parsed']:
                raise ValueError('Parsed answer is not original process answer')
        receipt = dict(status=envelope['status'], reply=reply,
            joins=envelope['joins'], error=envelope['error'],
            response_seen_ns=response_seen_ns, response_sha256=sha(blob),
            stdout_sha256=sha(stdout), stderr_sha256=sha(stderr),
            authority_granted=False, task_complete=False)
        write_sealed(self.out/slot/'client-receipt', encode(receipt))
        return receipt


class ExchangeHost:
    def __init__(self, directory, custody_directory, *, allocation,
                 freeze_sha256, executable_sha256, plans):
        self.out = Path(directory)
        self.plans = deepcopy(plans)
        self.bridge = HostBridge(custody_directory, allocation=allocation,
            freeze_sha256=freeze_sha256, executable_sha256=executable_sha256,
            slots=list(plans))
        self.consumed = set()

    @staticmethod
    def _argument(argv, flag):
        if argv.count(flag) != 1:
            raise ValueError('Exactly one trusted '+flag+' argument required')
        index = argv.index(flag)
        if index+1 >= len(argv):
            raise ValueError('Missing '+flag+' argument')
        return Path(argv[index+1])

    def serve(self, slot):
        if slot not in self.plans or slot in self.consumed or self.bridge.stopped:
            raise ValueError('Unknown/consumed/stopped host slot')
        directory = self.out/slot
        try:
            request_blob = read_sealed(directory/'request')
            if request_blob is None:
                return None
            # No later request may rescue this first consumed publication.
            self.consumed.add(slot)
            request = json.loads(request_blob)
            if request.get('slot') != slot:
                raise ValueError('Request slot mismatch')
            image = read_sealed(directory/'image', filename='payload.png')
            prompt = read_sealed(directory/'prompt')
            if image is None or prompt is None:
                raise ValueError('Published request without sealed artifacts')
            plan = self.plans[slot]
            argv = deepcopy(plan['argv'])
            image_path = self._argument(argv, '--image')
            schema_path = self._argument(argv, '--output-schema')
            if image_path.resolve() != (directory/'image/payload.png').resolve():
                raise ValueError('Trusted argv does not name actual exchanged image')
            before = dict(image_sha256=sha(image_path.read_bytes()),
                prompt_sha256=sha(prompt), schema_sha256=sha(schema_path.read_bytes()),
                executable_sha256=sha(Path(argv[0]).read_bytes()),
                argv_sha256=sha(encode(argv)))
            if (before['image_sha256'] != request['image_sha256']
                or before['schema_sha256'] != plan['schema_sha256']):
                raise ValueError('Image/schema identity changed before execution')
            reply = self.bridge.consume(request, argv=argv, prompt=prompt,
                image_bytes=image, timeout_seconds=plan['timeout_seconds'])
            # Original parsed response remains untouched, even after file drift.
            after = dict(image_sha256=sha(image_path.read_bytes()),
                prompt_sha256=sha((directory/'prompt/payload.bin').read_bytes()),
                schema_sha256=sha(schema_path.read_bytes()),
                executable_sha256=sha(Path(argv[0]).read_bytes()),
                argv_sha256=sha(encode(plan['argv'])))
            error = None if before == after else 'STOP_EXECUTED_ARTIFACT_CHANGED'
            envelope = dict(status='STOP' if error or reply['status']=='STOP' else 'returned',
                reply=reply, error=error, joins=dict(before=before, after=after),
                stdout_base64=base64.b64encode((self.bridge.out/slot/'stdout.bin').read_bytes()).decode(),
                stderr_base64=base64.b64encode((self.bridge.out/slot/'stderr.bin').read_bytes()).decode())
            self.bridge.stopped = True
            write_sealed(directory/'response', encode(envelope))
            if envelope['status'] == 'returned':
                self.bridge.stopped = False
            return envelope
        except Exception:
            self.consumed.add(slot)
            self.bridge.stopped = True
            raise


def main(plan_path):
    """Trusted host plan only; container requests cannot choose commands."""
    plan_blob = Path(plan_path).read_bytes()
    config = json.loads(plan_blob)
    seconds = config.pop('deadline_seconds')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Finite positive host deadline required')
    host = ExchangeHost(**config)
    write_sealed(host.bridge.out/'host-plan', plan_blob)
    deadline = time.monotonic()+seconds
    while len(host.consumed) != len(host.plans):
        if time.monotonic() >= deadline:
            host.bridge.stopped = True
            write_sealed(host.bridge.out/'host-stop', encode({'reason':'HOST_REQUEST_DEADLINE'}))
            return 1
        progressed = False
        for slot in host.plans:
            if slot not in host.consumed:
                response = host.serve(slot)
                if response is not None:
                    progressed = True
                    if response['status'] == 'STOP':
                        return 1
        if not progressed:
            time.sleep(0.01)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1]))
