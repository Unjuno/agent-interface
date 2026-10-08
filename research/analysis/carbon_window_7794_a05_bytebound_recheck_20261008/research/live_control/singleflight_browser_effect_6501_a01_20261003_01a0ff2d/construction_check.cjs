'use strict';
const assert=require('assert');
const {Broker,identity,admit}=require('./broker.cjs');
const base={verifier:'v',source:'s',target:'A',generation:1,digest:'d',predicate:'p',window:'w',role:'read_only'};
async function main(){
  let checks=0;
  for(const policy of ['independent','predicate','scoped']){
    let calls=0,release;const gate=new Promise(resolve=>release=resolve);
    const broker=new Broker(policy,()=>{}),read=()=>{calls++;return gate.then(()=>({scope:base,value:'READY'}));};
    const a=broker.get(base,read),b=broker.get({...base,target:'B'},read);
    await Promise.resolve();assert.equal(calls,policy==='predicate'?1:2);checks++;
    release();await Promise.all([a,b]);await Promise.resolve();assert.equal(broker.pending.size,0);checks++;
    await broker.get(base,read);assert.equal(calls,policy==='predicate'?2:3);checks++;
  }
  assert.equal(admit({scope:base,value:'READY'},base,base,9n,10n),'ELIGIBLE');checks++;
  assert.equal(admit({scope:base,value:'READY'},base,base,10n,10n),'DEADLINE');checks++;
  assert.equal(admit({scope:{...base,target:'B'},value:'READY'},base,base,1n,10n),'DISTINCT_SCOPE');checks++;
  assert.equal(admit({scope:base,value:'READY'},base,{...base,generation:2},1n,10n),'STALE_ON_RETURN');checks++;
  assert.equal(admit({scope:base,value:'UNKNOWN'},base,base,1n,10n),'UNKNOWN');checks++;
  assert.notEqual(identity(base),identity({...base,generation:true}));checks++;
  console.log(JSON.stringify({checks,errors:[]}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
