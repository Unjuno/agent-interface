"""Bounded passive source refresh; never relaxes signal-reader validity."""
import time

class SourceRefreshRefused(RuntimeError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__('source refresh refused: ' + receipt['reason'])

def refresh_source(observation, health_reader, ammo_reader, send, wait, prefix,
                   max_refreshes=4, budget_seconds=2, clock=time.monotonic,
                   lease_clock=time.perf_counter_ns):
    if type(max_refreshes) is not int or not 1 <= max_refreshes <= 4:
        raise ValueError('one to four passive refreshes required')
    if not 0 < budget_seconds <= 2:
        raise ValueError('positive source-refresh budget at most two seconds required')
    receipt = {'format':'doom-source-refresh-v1', 'status':'pending',
               'source_sequence':observation.get('sequence'), 'attempts':[]}
    def refuse(reason):
        receipt.update(status='refused', reason=reason)
        raise SourceRefreshRefused(receipt)
    def valid(row):
        health, ammo = health_reader.read(row), ammo_reader.read(row)
        for name, signal, minimum in [('health',health,1), ('ammo',ammo,0)]:
            status = signal.get('status')
            if status == 'observed':
                if type(signal.get('value')) is not int or signal['value'] < minimum:
                    refuse('invalid_observed_' + name)
            elif status != 'unknown':
                refuse('invalid_signal_status_' + name)
        return health['status'] == 'observed' and ammo['status'] == 'observed'
    if valid(observation):
        receipt['status']='already_observed'
        return observation, receipt
    deadline = clock() + budget_seconds
    def remaining():
        left = deadline - clock()
        if left <= 0: refuse('deadline_expired')
        return left
    current = observation
    for index in range(max_refreshes):
        left = remaining()
        identifier = f'{prefix}-{index}'
        command = {'op':'submit','id':identifier,'expected_sequence':current['sequence'],
                   'valid_until_ns':lease_clock()+int(left*1e9), 'steps':[{'op':'observe'}]}
        attempt = {'id':identifier,'expected_sequence':current['sequence'], 'command':command}
        receipt['attempts'].append(attempt)
        try:
            send(command)
            accepted = wait(lambda r: (r.get('event') == 'accepted' and r.get('id') == identifier)
                            or r.get('event') == 'rejected', timeout=remaining())
            attempt['acceptance']=accepted
            if accepted.get('event') != 'accepted': refuse('refresh_rejected')
            fresh = wait(lambda r:r.get('event') == 'observation' and r.get('id') == identifier,
                         timeout=remaining())
            attempt['observation_sequence']=fresh.get('sequence')
            terminal = wait(lambda r:r.get('event') == 'terminal' and r.get('id') == identifier,
                            timeout=remaining())
            attempt['terminal']=terminal
        except SourceRefreshRefused:
            raise
        except Exception as error:
            receipt.update(status='refused', reason='transport_or_observation_failure', error_type=type(error).__name__)
            raise SourceRefreshRefused(receipt) from error
        remaining()
        release = terminal.get('release',{})
        if (terminal.get('status') != 'completed' or release.get('verified') is not True
                or release.get('keys_down') != [] or release.get('buttons_down') != []
                or type(accepted.get('intent_token')) is not str or not accepted['intent_token']
                or release.get('intent_token') != accepted['intent_token']):
            refuse('refresh_release_unqualified')
        if (type(fresh.get('sequence')) is not int or fresh['sequence'] <= current['sequence']
                or type(fresh.get('capture_ns')) is not int or fresh['capture_ns'] <= current['capture_ns']
                or fresh.get('pointer_binding') != observation.get('pointer_binding')):
            refuse('fresh_observation_unqualified')
        current = fresh
        if valid(current):
            receipt.update(status='recovered', recovered_sequence=current['sequence'])
            return current, receipt
    refuse('refresh_limit_exhausted')
