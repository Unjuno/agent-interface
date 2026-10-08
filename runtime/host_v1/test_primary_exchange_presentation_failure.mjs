/** Post-effect presentation persistence must retain evidence and prevent replay. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createPrimaryExchange} from './primary_exchange.mjs';

test('presentation persistence failure retains original reply and blocks another command', async () => {
  const parent = await mkdtemp(join(tmpdir(), 'primary-exchange-presentation-'));
  const directory = join(parent, 'exchange');
  const reply = {attempt: 1, result: {isError: false,
    content: [{type: 'text', text: '{"status":"observed"}'}]}};
  let calls = 0;
  const host = {
    sendPresented: async () => { calls++; return reply; },
    review: async (_attempt, value) => value,
    acknowledgeText: async (_attempt, value) => value,
    present: async () => {},
  };
  const exchange = await createPrimaryExchange({host, directory, route: 'guarded-local'});
  const request = {id: 1, method: 'observe', args: []};
  const presentationPath = join(directory, 'presentation-1.json');
  await writeFile(presentationPath, 'occupied');

  await assert.rejects(exchange.execute(request), /EEXIST/);

  assert.equal(calls, 1);
  assert.deepEqual(JSON.parse(await readFile(join(directory, 'request-1.json'))), request);
  assert.deepEqual(JSON.parse(await readFile(join(directory, 'original-reply-1.json'))), reply);
  assert.equal(await readFile(presentationPath, 'utf8'), 'occupied');
  assert.ok(exchange.state().stopped);
  assert.equal(exchange.state().next_id, 2);
  await assert.rejects(exchange.execute({id: 2, method: 'observe', args: []}), /exchange stopped/);
  assert.equal(calls, 1);
});
