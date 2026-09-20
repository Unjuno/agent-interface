"""Bounded process integration check; barriers are test coordination, never ACKs."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys

from research.integration.event_inbox_reader_v1.reader import read_pending
from research.live_control.delivery_ledger_v2 import DeliveryLedger

MODULE = 'research.integration.event_inbox_reader_v1.active_check'
STREAM = 'owned-component-check-1'


def producer(root):
    ledger = DeliveryLedger()
    records = [ledger.prepare({'event': name, 'payload': {'value': n}})
               for n, name in enumerate(('ready', 'observation', 'terminal'))]
    encoded = [json.dumps(record).encode('utf-8') for record in records]
    (root / 'expected.json').write_text(json.dumps(records), encoding='utf-8')
    with (root / 'delivered.jsonl').open('xb') as output:
        output.write(encoded[0] + b'\n' + encoded[1])
        output.flush()
        print('partial-ready', flush=True)
        if sys.stdin.readline().strip() != 'continue-test':
            raise RuntimeError('missing test barrier')
        output.write(b'\n' + encoded[2] + b'\n')
        output.flush()
    print('complete', flush=True)


def reader(root):
    cursor_path = root / 'cursor.json'
    cursor = json.loads(cursor_path.read_text()) if cursor_path.exists() else None
    print(json.dumps(read_pending(root / 'delivered.jsonl', stream_id=STREAM,
                                  cursor=cursor)))


async def check(root):
    root.mkdir(parents=True, exist_ok=False)
    children = []
    async def spawn(mode):
        child = await asyncio.create_subprocess_exec(
            sys.executable, '-m', MODULE, mode, str(root),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        children.append(child)
        return child

    async def read_once(label):
        child = await spawn('read')
        stdout, stderr = await asyncio.wait_for(child.communicate(), 5)
        (root / (label + '.stdout.json')).write_bytes(stdout)
        (root / (label + '.stderr.txt')).write_bytes(stderr)
        assert child.returncode == 0, stderr
        result = json.loads(stdout)
        assert result['authority'] == 'none'
        assert result['acknowledged'] is False and result['input_dispatched'] is False
        assert result['problem'] is None
        return result

    writer = await spawn('produce')
    try:
        barrier = await asyncio.wait_for(writer.stdout.readline(), 5)
        (root / 'producer.barrier.txt').write_bytes(barrier)
        assert barrier.rstrip(b'\r\n') == b'partial-ready'
        first = await read_once('first')
        assert len(first['records']) == 1 and first['tail_state'] == 'incomplete'
        (root / 'cursor.json').write_text(json.dumps(first['next_cursor']))
        pending = await read_once('pending')
        assert pending['records'] == [] and pending['tail_state'] == 'incomplete'
        assert pending['next_cursor'] == first['next_cursor']
        assert await read_once('repeated') == pending
        writer.stdin.write(b'continue-test\n')
        await asyncio.wait_for(writer.stdin.drain(), 5)
        stdout, stderr = await asyncio.wait_for(writer.communicate(), 5)
        (root / 'producer.stdout.txt').write_bytes(barrier + stdout)
        (root / 'producer.stderr.txt').write_bytes(stderr)
        assert writer.returncode == 0 and stdout.rstrip(b'\r\n') == b'complete', stderr
        resumed = await read_once('resumed')
        expected = json.loads((root / 'expected.json').read_text())
        assert first['records'] + resumed['records'] == expected
        assert resumed['tail_state'] == 'end'
        (root / 'cursor.json').write_text(json.dumps(resumed['next_cursor']))
        final = await read_once('final')
        assert final['records'] == [] and final['tail_state'] == 'end'
        assert final['next_cursor'] == resumed['next_cursor']
        report = {'status': 'PASS', 'records': len(expected), 'reader_processes': 5,
                  'scope': 'active append producer component; no GUI/model/ACK proof',
                  'stream_sha256': hashlib.sha256((root / 'delivered.jsonl').read_bytes()).hexdigest()}
        (root / 'result.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
    finally:
        for child in children:
            if child.returncode is None:
                child.kill()
            await asyncio.wait_for(child.wait(), 5)


if __name__ == '__main__':
    mode, directory = sys.argv[1:]
    root = Path(directory)
    if mode == 'produce':
        producer(root)
    elif mode == 'read':
        reader(root)
    elif mode == 'check':
        asyncio.run(check(root))
    else:
        raise ValueError('unknown mode')
