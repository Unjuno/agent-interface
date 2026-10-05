import test from 'node:test';
import assert from 'node:assert/strict';
import {createPrimaryCaller} from './primary_caller.mjs';

function fixture() {
  const calls=[];
  const response={result:{isError:false,content:[{type:'text',text:JSON.stringify({status:'minted',source_sequence:1,minted:[{alias:'note'}]})}]}};
  const caller=createPrimaryCaller({sendPresented:async(tool,args)=>{calls.push({tool,args});return response;}},'guarded-local',{});
  return {calls,response,caller};
}
const cases=[...['point','region'].flatMap(field=>['hole','undefined'].flatMap(kind=>['first','second','both'].map(position=>field+'-'+kind+'-'+position))), 'null-point','nan-point','unsafe-point','fractional-point','region-low','region-high'];
function values(name) {
  const point=[20,30],region=[24,38];
  if(name.includes('-hole-')||name.includes('-undefined-')) {
    const target=name.startsWith('point')?point:region;
    for(const i of name.endsWith('first')?[0]:name.endsWith('second')?[1]:[0,1]) {
      if(name.includes('-hole-'))delete target[i];else target[i]=undefined;
    }
  } else if(name==='null-point')point[0]=null;
  else if(name==='nan-point')point[0]=NaN;
  else if(name==='unsafe-point')point[0]=Number.MAX_SAFE_INTEGER+1;
  else if(name==='fractional-point')point[0]=1.5;
  else if(name==='region-low')region[0]=3;
  else if(name==='region-high')region[1]=97;
  return {point,region};
}
for(const name of cases)test('single mint rejects '+name+' before host entry and preserves close',async()=>{
  const {caller,calls}=fixture();const {point,region}=values(name);
  await assert.rejects(caller.mint('note',1,point,region),/invalid primary mint arguments/);
  assert.equal(caller.state().stopped,'invalid primary mint arguments');
  await assert.rejects(caller.call('interface_clock',{}),/trial stopped/);
  assert.deepEqual(calls,[]);
  await caller.call('interface_close',{});
  assert.deepEqual(calls.map(c=>c.tool),['interface_close']);
});
test('single mint accepts dense safe pairs and snapshots their arguments',async()=>{
  const {caller,calls,response}=fixture();const point=[20,30],region=[24,38];
  assert.equal(await caller.mint('note',1,point,region),response);
  point[0]=999;region[1]=99;
  assert.deepEqual(calls,[{tool:'interface_guarded_mint',args:{alias:'note',source_sequence:1,point:[20,30],region_size:[24,38]}}]);
  assert.equal(caller.state().stopped,null);
  await caller.call('interface_clock',{});
  await caller.call('interface_close',{});
  assert.deepEqual(calls.map(c=>c.tool),['interface_guarded_mint','interface_clock','interface_close']);
});
for(const name of cases.filter(n=>n.includes('-hole-')))test('batch mint still rejects '+name+' before host entry',async()=>{
  const {caller,calls}=fixture();const {point,region}=values(name);
  await assert.rejects(caller.mintMany(1,[{alias:'note',point,region_size:region}]),/invalid primary batch mint arguments/);
  assert.equal(caller.state().stopped,'invalid primary batch mint arguments');
  await assert.rejects(caller.call('interface_clock',{}),/trial stopped/);
  assert.deepEqual(calls,[]);
  await caller.call('interface_close',{});
  assert.deepEqual(calls.map(c=>c.tool),['interface_close']);
});
test('batch mint keeps healthy dense reference registration',async()=>{
  const {caller,calls,response}=fixture();
  assert.equal(await caller.mintMany(1,[{alias:'note',point:[20,30],region_size:[24,38]}]),response);
  assert.equal(caller.state().stopped,null);
  assert.deepEqual(calls,[{tool:'interface_guarded_mint_many',args:{source_sequence:1,references:[{alias:'note',point:[20,30],region_size:[24,38]}]}}]);
});
