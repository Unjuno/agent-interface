"""Wait for one response or an atomically published host-failure marker."""
import json,time

class HostFailure(RuntimeError):
    def __init__(self, error_type=None, completed_calls=None):
        self.error_type = error_type
        self.completed_calls = completed_calls
        super().__init__('host failed before response; effect and usage may be unknown')

def wait_response(response, failure, *, timeout=120.0, interval=.05,
                  clock=time.monotonic, sleep=time.sleep):
    if timeout <= 0 or interval <= 0:
        raise ValueError('positive timeout and interval required')
    deadline = clock() + timeout
    while True:
        # A completed response is the stronger result if both are visible.
        if response.is_file():
            return json.loads(response.read_text())
        if failure.is_file():
            try:
                marker = json.loads(failure.read_text())
                if (type(marker) is not dict or marker.get('kind') != 'host_failed'
                        or type(marker.get('error_type')) is not str
                        or not 0 < len(marker['error_type']) <= 64
                        or type(marker.get('completed_calls')) is not int
                        or marker['completed_calls'] < 0):
                    raise ValueError('invalid host marker')
                raise HostFailure(marker['error_type'], marker['completed_calls'])
            except (ValueError, OSError):
                raise HostFailure() from None
        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError('host response not observed')
        sleep(min(interval, remaining))
