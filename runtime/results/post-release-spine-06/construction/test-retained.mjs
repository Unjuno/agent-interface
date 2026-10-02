import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createPrimaryTrialCaller} from './primary-policy.mjs';
const original=JSON.parse(await readFile(new URL('./retained-direct-success.json',import.meta.url),'utf8'));
function setup(reply){return createPrimaryTrialCaller({sendPresented:async()=>reply,review:async()=>{}},'direct-post',{});}
{
 const c=setup(original);assert.equal(await c.call('interface_dispatch',{}),original);assert.equal(c.state().stopped,null,'actual dispatch-summary success must remain usable');
}
for(const mutate of [m=>m.outcome_summary.input_release_verified=false,m=>m.receipt.execution_summary.releases[0].keys_down=['CTRL'],m=>m.outcome_summary.execution_status='execution_failed',m=>m.image_status='unavailable']){
 const r=structuredClone(original);const m=JSON.parse(r.result.content[0].text);mutate(m);r.result.content[0].text=JSON.stringify(m);
 const c=setup(r);assert.equal(await c.call('interface_dispatch',{}),r);assert.ok(c.state().stopped,'altered real outcome must stop');
}
console.log('PASS actual retained dispatch summary and release/failure/image mutations');
