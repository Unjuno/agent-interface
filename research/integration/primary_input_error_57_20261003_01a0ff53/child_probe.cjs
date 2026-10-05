/* Ordinary inert Node stream probe; no uncaughtException hook or native host. */
const {PassThrough} = require('node:stream');
const scenario = process.env.PRIMARY_READ_SCENARIO;
const turn = () => new Promise(resolve => setImmediate(resolve));
const emit = value => process.stdout.write(JSON.stringify(value) + '\n');
(async () => {
  const {servePrimaryLines} = await import('./runtime/host_v1/primary_stdio.mjs');
  const input = new PassThrough(), output = new PassThrough();
  let finish, calls = 0, completed = 0, settled = false;
  output.on('data', chunk => emit({kind: 'response', value: JSON.parse(chunk.toString())}));
  const exchange = {
    state: () => ({next_id: calls + 1}),
    execute: async request => {
      calls++; emit({kind: 'execute_enter', request});
      await new Promise(resolve => {finish = resolve;});
      completed++; emit({kind: 'execute_exit', outcome: scenario === 'pending_failure' ? 'rejected' : 'returned'});
      if (scenario === 'pending_failure') throw Error('inert command outcome unavailable');
      return {id: 1, value: 'original result'};
    }
  };
  const pending = servePrimaryLines({exchange, input, output}).then(
    () => {settled = true; emit({kind: 'owner_resolved'});},
    error => {settled = true; emit({kind: 'owner_rejected', message: error.message}); process.exitCode = 2;}
  );
  if (scenario !== 'before_request') {
    input.write('{"id":1,"method":"call","args":[]}\n');
    await turn();
  }
  if (scenario === 'eof_pending') {
    emit({kind: 'eof_issued'}); input.end();
  } else {
    emit({kind: 'input_error_issued'}); input.destroy(Error('inert input read failure'));
  }
  await turn();
  emit({kind: 'checkpoint', calls, completed, settled});
  if (scenario !== 'before_request') finish();
  await pending;
  emit({kind: 'final', calls, completed, settled});
})().catch(error => {console.error(String(error)); process.exitCode = 3;});
