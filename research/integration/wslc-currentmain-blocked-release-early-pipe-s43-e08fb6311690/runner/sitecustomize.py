"""S42-only fault injector: force two early false supervisor pipe polls."""
import json, os, time
from pathlib import Path
if os.environ.get('AGENT_INTERFACE_MCP_XVFB_EARLY_POLL_TRACE'):
    from runtime.guarded_x11_v1.cancel_supervisor import PrestartedCancellationSupervisor
    _original_run = PrestartedCancellationSupervisor.run
    def _run_with_early_poll(self, request, *, deadline_monotonic_ns):
        original_receive = self._receive
        trace = []
        class ReceiveProxy:
            def poll(proxy, timeout):
                index = len(trace) + 1
                if index <= 2:
                    trace.append({'index':index,'requested_timeout_s':timeout,
                                  'returned':False,'forced_early_timeout':True,
                                  'monotonic_ns':time.monotonic_ns()})
                    return False
                returned = original_receive.poll(timeout)
                trace.append({'index':index,'requested_timeout_s':timeout,
                              'returned':returned,'forced_early_timeout':False,
                              'monotonic_ns':time.monotonic_ns()})
                return returned
            def __getattr__(proxy, name): return getattr(original_receive, name)
        proxy = ReceiveProxy()
        self._receive = proxy
        try:
            return _original_run(self, request,
                                 deadline_monotonic_ns=deadline_monotonic_ns)
        finally:
            self._receive = original_receive
            path = Path(os.environ['AGENT_INTERFACE_MCP_XVFB_EARLY_POLL_TRACE'])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'pid':os.getpid(),
                'operation_id':request.get('operation_id'),
                'forced_early_timeout_count':sum(1 for row in trace if row['forced_early_timeout']),
                'polls':trace}, sort_keys=True, indent=2), encoding='utf-8')
    PrestartedCancellationSupervisor.run = _run_with_early_poll
