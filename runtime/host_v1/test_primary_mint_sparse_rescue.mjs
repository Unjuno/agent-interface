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
