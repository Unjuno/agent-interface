import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

test('single mint rejects a sparse coordinate pair before host dispatch', async () => {
  const calls = [];
  const caller = createPrimaryCaller({
    sendPresented: async (tool, args) => {
      calls.push({tool, args});
      return {result:{isError:false,content:[{type:'text',text:'{"status":"minted"}'}]}};
    }
  }, 'guarded-local', {});
  const point = [20, 30];
  delete point[0];

  await assert.rejects(caller.mint('note', 1, point, [24, 38]), /invalid primary mint arguments/);
  assert.deepEqual(calls, []);
});

test('single mint validates and dispatches one indexed coordinate snapshot', async () => {
  const calls = [];
  let iteratorCalls = 0;
  const point = [20, 30];
  point[Symbol.iterator] = function* () {
    yield iteratorCalls++ === 0 ? 20 : Number.NaN;
    yield 30;
  };
  const caller = createPrimaryCaller({
    sendPresented: async (tool, args) => {
      calls.push({tool, args});
      return {result:{isError:false,content:[{type:'text',text:'{"status":"minted"}'}]}};
    }
  }, 'guarded-local', {});

  await caller.mint('note', 1, point, [24, 38]);
  assert.equal(iteratorCalls, 0);
  assert.deepEqual(calls[0].args.point, [20, 30]);
});

test('input dispatches the same indexed offset values it validated', async () => {
  const calls = [];
  let iteratorCalls = 0;
  const offset = [10, 20];
  offset[Symbol.iterator] = function* () {
    yield iteratorCalls++ === 0 ? 10 : Number.NaN;
    yield 20;
  };
  const caller = createPrimaryCaller({
    sendPresented: async (tool, args) => {
      calls.push({tool, args});
      return {result:{isError:false,content:[{type:'text',text:'{}'}]}};
    }
  }, 'guarded-local', {});

  await caller.input('field', offset, 'click', []);
  assert.equal(iteratorCalls, 0);
  assert.deepEqual(calls[0].args.offset, [10, 20]);
});

test('batch mint rejects sparse indexed coordinates even when an iterator fills them', async () => {
  const calls = [];
  const point = new Array(2);
  point[Symbol.iterator] = function* () { yield 20; yield 30; };
  const caller = createPrimaryCaller({
    sendPresented: async (tool, args) => {
      calls.push({tool, args});
      return {result:{isError:false,content:[{type:'text',text:'{"status":"minted","source_sequence":1,"minted":[{"alias":"note"}]}'}]}};
    }
  }, 'guarded-local', {});

  await assert.rejects(caller.mintMany(1, [
    {alias:'note', point, region_size:[24, 38]}
  ]), /invalid primary batch mint arguments/);
  assert.deepEqual(calls, []);
});
