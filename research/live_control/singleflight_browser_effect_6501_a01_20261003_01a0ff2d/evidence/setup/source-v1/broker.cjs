'use strict';
function identity(scope) {
  return JSON.stringify([scope.verifier, scope.source, scope.target, scope.generation,
    scope.digest, scope.predicate, scope.window, scope.role]);
}
class Broker {
  constructor(policy, record) { this.policy=policy; this.record=record; this.pending=new Map(); }
  get(scope, read) {
    const key=this.policy==='predicate' ? scope.predicate : identity(scope);
    if(this.policy!=='independent' && this.pending.has(key)) {
      this.record({event:'join',key,scope}); return this.pending.get(key);
    }
    this.record({event:'spawn',key,scope});
    const work=Promise.resolve().then(read);
    if(this.policy!=='independent') {
      this.pending.set(key,work);
      work.finally(()=>{if(this.pending.get(key)===work)this.pending.delete(key);}).catch(()=>{});
    }
    return work;
  }
}
function admit(result, requested, current, now, deadline) {
  if(now>=deadline)return 'DEADLINE';
  if(identity(result.scope)!==identity(requested))return 'DISTINCT_SCOPE';
  if(result.value!=='READY')return 'UNKNOWN';
  if(identity(current)!==identity(requested))return 'STALE_ON_RETURN';
  return 'ELIGIBLE';
}
module.exports={Broker,identity,admit};
