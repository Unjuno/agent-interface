"""Small MAP01 session boundary for identity-bound input-owner generations."""


class InputOwnerGenerationProtocol:
    MAX_REFRESH_ATTEMPTS = 4

    def __init__(self):
        self._latest_terminal_id = None
        self._latest_terminal = None
        self._refresh_required = None
        self._refresh_attempts = 0

    def record_terminal(self, row, backend):
        if type(row) is not dict or row.get('event') != 'terminal':
            return row
        identifier = row.get('id')
        if type(identifier) is not str or not identifier:
            return row
        if hasattr(backend, '_owner_generation'):
            row['input_owner_generation'] = backend._owner_generation
            row['input_owner_id'] = backend.owner.owner_id
        self._latest_terminal_id = identifier
        self._latest_terminal = dict(row)
        return row

    def rotate(self, command, *, executor, backend, executor_factory):
        if (type(command) is not dict or set(command) != {'op', 'id'}
                or command.get('op') != 'rotate_input_owner'
                or type(command.get('id')) is not str):
            raise ValueError('exact owner rotation command required')
        identifier = command['id']
        terminal = self._latest_terminal
        if terminal is None or identifier != self._latest_terminal_id:
            raise ValueError('latest published terminal required for owner rotation')
        rotate = getattr(backend, 'rotate_input_owner_after_cancel', None)
        if not callable(rotate):
            raise ValueError('selected backend does not support owner rotation')
        executor.close()
        try:
            receipt = rotate(terminal)
            replacement = executor_factory(backend)
        except BaseException as error:
            raise RuntimeError('owner generation rotation failed closed') from error
        if (type(receipt) is not dict or receipt.get('event') != 'input_owner_generation'
                or receipt.get('terminal_id') != identifier
                or receipt.get('previous_generation') != terminal.get('input_owner_generation')
                or type(receipt.get('generation')) is not int
                or receipt.get('generation') != terminal.get('input_owner_generation', -1) + 1
                or receipt.get('previous_owner_id') != terminal.get('input_owner_id')
                or type(receipt.get('owner_id')) is not str or not receipt['owner_id']
                or receipt.get('owner_id') == receipt.get('previous_owner_id')
                or receipt.get('source_invalidated') is not True
                or receipt.get('grants_input_authority') is not False):
            try:
                replacement.close()
            except BaseException as close_error:
                raise BaseExceptionGroup(
                    'malformed rotation receipt and replacement close failed',
                    [RuntimeError('owner generation receipt invalid'), close_error])
            raise RuntimeError('owner generation rotation receipt invalid')
        self._refresh_required = identifier
        self._refresh_attempts = 0
        return replacement, receipt

    def refresh_source(self, command, *, backend):
        if (type(command) is not dict or set(command) != {'op', 'id'}
                or command.get('op') != 'refresh_owner_source'
                or type(command.get('id')) is not str
                or command.get('id') != self._refresh_required):
            raise ValueError('matching post-rotation source refresh required')
        if self._refresh_attempts >= self.MAX_REFRESH_ATTEMPTS:
            raise ValueError('post-rotation source refresh limit exhausted')
        snapshot = getattr(backend, 'snapshot', None)
        if not callable(snapshot):
            raise ValueError('selected backend cannot capture a source observation')
        generation = getattr(backend, '_owner_generation', None)
        owner = getattr(backend, 'owner', None)
        owner_id = getattr(owner, 'owner_id', None)
        if (type(generation) is not int or type(owner_id) is not str or not owner_id
                or getattr(backend, '_source_identity', None) is not None):
            raise ValueError('post-rotation source state is not invalidated')
        self._refresh_attempts += 1
        observation_id = f'owner-generation-source-{generation}-{self._refresh_attempts}'
        snapshot(observation_id, 0)
        source = getattr(backend, '_source_identity', None)
        binding = getattr(backend, 'observed_pointer', None)
        if (type(source) is not tuple or source[0] != backend.sequence
                or type(binding) is not dict
                or source[1] != binding.get('surface')
                or getattr(backend, 'observed_focus', None) != binding.get('focus')):
            raise RuntimeError('fresh identity-bound source was not established')
        attempt = self._refresh_attempts
        self._refresh_required = None
        self._refresh_attempts = 0
        return {'event': 'input_owner_source_refreshed',
                'terminal_id': command['id'], 'generation': generation,
                'owner_id': owner_id, 'observation_id': observation_id,
                'attempt': attempt,
                'sequence': source[0], 'surface': source[1], 'digest': source[2],
                'source_invalidated': False, 'grants_input_authority': False}
