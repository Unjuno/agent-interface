"""Isolated read-only executor lifetime construction; no runtime imports."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import threading
import time

WAIT_SECONDS = 3


class Trace:
    def __init__(self):
        self.rows = []
        self.lock = threading.Lock()
        self.active = 0

    def event(self, kind, **fields):
        with self.lock:
            self.rows.append(dict(sequence=len(self.rows), event=kind, **fields))

    def worker_event(self, kind, producer):
        with self.lock:
            self.active += 1 if kind == 'worker_enter' else -1
            self.rows.append(dict(sequence=len(self.rows), event=kind,
                producer=producer, active_callables=self.active))


class Bank:
    def __init__(self, loop, trace):
        self.loop, self.trace = loop, trace
        self.gates, self.entered = {}, {}

    def reserve(self, producer):
        self.gates[producer] = threading.Event()
        self.entered[producer] = asyncio.Event()

    def read(self, producer):
        self.trace.worker_event('worker_enter', producer)
        self.loop.call_soon_threadsafe(self.entered[producer].set)
        try:
            if not self.gates[producer].wait(WAIT_SECONDS):
                raise TimeoutError('authored barrier was not released')
            return {'producer': producer, 'payload': 'read-only-fixture'}
        finally:
            self.trace.worker_event('worker_exit', producer)

    async def wait_enter(self, producer):
        await asyncio.wait_for(self.entered[producer].wait(), WAIT_SECONDS)

    def open(self, producer):
        self.trace.event('gate_open', producer=producer)
        self.gates[producer].set()


@dataclass
class Entry:
    producer: int
    future: object
    task: object = None
    waiters: int = 0
    closing: bool = False


class Broker:
    def __init__(self, retain_until_future):
        self.loop = asyncio.get_running_loop()
        self.trace = Trace()
        self.bank = Bank(self.loop, self.trace)
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.retain_until_future = retain_until_future
        self.entry = None
        self.entries = []
        self.attachments = 0
        self.requests = 0
        self.changed = asyncio.Event()
        self.callers = []

    async def _await_worker(self, entry):
        try:
            value = await asyncio.wrap_future(entry.future)
        except asyncio.CancelledError:
            self.trace.event('wrapper_terminal', producer=entry.producer, status='cancelled')
            raise
        else:
            self.trace.event('wrapper_terminal', producer=entry.producer, status='completed')
            return value

    def _retire(self, entry, reason):
        if self.entry is entry:
            self.entry = None
            self.trace.event('registry_drop', producer=entry.producer, reason=reason)

    def _acknowledge(self, entry):
        self.trace.event('future_done', producer=entry.producer,
            done=entry.future.done(), running=entry.future.running())
        self._retire(entry, 'future_done')
        self.changed.set()

    def _new_entry(self):
        producer = len(self.entries) + 1
        self.bank.reserve(producer)
        self.trace.event('producer_submitted', producer=producer)
        entry = Entry(producer, self.executor.submit(self.bank.read, producer))
        self.entries.append(entry)
        self.entry = entry
        entry.task = asyncio.create_task(self._await_worker(entry))
        entry.future.add_done_callback(lambda unused: self.loop.call_soon_threadsafe(self._acknowledge, entry))
        return entry

    async def read(self, caller):
        self.trace.event('request', caller=caller)
        self.requests += 1
        self.changed.set()
        entry = self.entry
        if entry is not None and entry.closing:
            if not entry.future.done():
                self.trace.event('caller_yield', caller=caller, reason='producer_exit_pending')
                return 'YIELD'
            self._retire(entry, 'future_done_observed')
            entry = None
        if entry is None:
            entry = self._new_entry()
        entry.waiters += 1
        self.attachments += 1
        self.trace.event('attach', caller=caller, producer=entry.producer, waiters=entry.waiters)
        self.changed.set()
        try:
            value = await asyncio.shield(entry.task)
            self.trace.event('caller_deliver', caller=caller, producer=value['producer'])
            return value
        except asyncio.CancelledError:
            self.trace.event('caller_cancelled', caller=caller)
            raise
        finally:
            entry.waiters -= 1
            self.trace.event('detach', caller=caller, producer=entry.producer, waiters=entry.waiters)
            if not entry.waiters and not entry.future.done():
                entry.closing = True
                entry.task.cancel()
                if not self.retain_until_future:
                    self._retire(entry, 'last_detach_wrapper_cancel')
            self.changed.set()

    def start(self, caller):
        task = asyncio.create_task(self.read(caller))
        self.callers.append(task)
        return task

    async def attached(self, count):
        while self.attachments < count:
            self.changed.clear()
            await asyncio.wait_for(self.changed.wait(), WAIT_SECONDS)

    async def requested(self, count):
        while self.requests < count:
            self.changed.clear()
            await asyncio.wait_for(self.changed.wait(), WAIT_SECONDS)

    async def join_workers(self):
        await asyncio.wait_for(asyncio.gather(*(asyncio.wrap_future(e.future) for e in self.entries)), WAIT_SECONDS)
        await asyncio.sleep(0)

    async def cleanup(self):
        for producer in self.bank.gates:
            self.bank.gates[producer].set()
        try:
            await asyncio.gather(*self.callers, return_exceptions=True)
            await asyncio.gather(*(e.task for e in self.entries), return_exceptions=True)
            await self.join_workers()
        finally:
            self.executor.shutdown(wait=True, cancel_futures=True)
        # shutdown joins callback dispatch; flush its queued event-loop acknowledgments.
        await asyncio.sleep(0)
        self.trace.event('cleanup', active_callables=self.trace.active,
            wrappers_done=all(e.task.done() for e in self.entries),
            futures_done=all(e.future.done() for e in self.entries),
            registry_empty=self.entry is None, executor_shutdown=True)


async def run_case(policy, schedule):
    broker = Broker(policy == 'future_ack')
    first, second = broker.start('first'), broker.start('second')
    try:
        await broker.attached(2)
        await broker.bank.wait_enter(1)
        original = broker.entries[0]
        if schedule == 'stable_pair':
            broker.bank.open(1)
            await asyncio.gather(first, second)
        elif schedule == 'one_detach':
            first.cancel()
            await asyncio.gather(first, return_exceptions=True)
            third = broker.start('rejoin')
            await broker.attached(3)
            broker.bank.open(1)
            await asyncio.gather(second, third)
        else:
            first.cancel()
            second.cancel()
            await asyncio.gather(first, second, return_exceptions=True)
            await asyncio.gather(original.task, return_exceptions=True)
            broker.trace.event('after_last_detach', wrapper_done=original.task.done(),
                wrapper_cancelled=original.task.cancelled(), future_done=original.future.done(),
                future_running=original.future.running(), active_callables=broker.trace.active,
                registry_present=broker.entry is original,
                registry_closing=broker.entry is original and original.closing)
            if schedule == 'early_rejoin':
                third = broker.start('rejoin')
                await broker.requested(3)
                if len(broker.entries) == 2:
                    await broker.attached(3)
                    await broker.bank.wait_enter(2)
                for producer in list(broker.bank.gates):
                    broker.bank.open(producer)
                await asyncio.gather(third)
            elif schedule == 'post_exit_rejoin':
                broker.bank.open(1)
                await broker.join_workers()
                third = broker.start('rejoin')
                await broker.attached(3)
                await broker.bank.wait_enter(2)
                broker.bank.open(2)
                await third
            else:
                raise ValueError('unknown schedule')
    finally:
        await broker.cleanup()
    return {'policy': policy, 'schedule': schedule, 'events': broker.trace.rows}
