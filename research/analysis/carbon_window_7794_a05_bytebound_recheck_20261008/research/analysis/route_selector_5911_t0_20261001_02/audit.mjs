const argmin = rows => { const m = Math.min(...rows.map(x => x.cost)); return rows.filter(x => x.cost === m).map(x => x.id).sort(); };
export function audit(fixture,raw) {
 const errors=[];
 if(raw.schema!=="route-selector-explicit-5911-candidate-v1")errors.push("schema");
 if(raw.selector!=="minimum_total_cost"||raw.selector!==fixture.selector)errors.push("selector");
 if(raw.tie_policy!==fixture.tie_policy)errors.push("tie_policy");
 if(!Array.isArray(raw.rows)||raw.rows.length!==fixture.cases.length)errors.push("row_count");
 for(let i=0;i<fixture.cases.length;i++){
  const c=fixture.cases[i],r=raw.rows?.[i]; if(!r||r.case_id!==c.id){errors.push(c.id+":identity");continue}
  const before=c.routes.map(x=>({id:x.id,cost:x.cost})),after=c.routes.map(x=>({id:x.id,cost:x.cost+c.delta[x.id]}));
  const pre=argmin(before),post=argmin(after),same=JSON.stringify(pre)===JSON.stringify(post);
  const status=same?"FIXED_TOPOLOGY":"NONSTATIONARY_INTERVENTION",delta=same?Math.min(...before.map(x=>x.cost))-Math.min(...after.map(x=>x.cost)):null;
  if(JSON.stringify(r.before)!==JSON.stringify({routes:before,selected:pre,endpoint_cost:Math.min(...before.map(x=>x.cost))}))errors.push(c.id+":before");
  if(JSON.stringify(r.after)!==JSON.stringify({routes:after,selected:post,endpoint_cost:Math.min(...after.map(x=>x.cost))}))errors.push(c.id+":after");
  if(r.status!==status)errors.push(c.id+":status");
  if(r.endpoint_delta!==delta)errors.push(c.id+":delta");
 }
 const mutations=[];
 for(const field of ["status","endpoint_delta","selected"]){
  const changed=JSON.parse(JSON.stringify(raw));
  if(field==="selected") changed.rows[0].after.selected=["alternate"];
  else if(field==="status")changed.rows[2].status="FIXED_TOPOLOGY";
  else changed.rows[2].endpoint_delta=50;
  const caught=JSON.stringify(auditCore(fixture,changed))!=="[]";
  mutations.push({field,rejected:caught});
 }
 return {status:errors.length===0&&mutations.every(x=>x.rejected)?"PASS_METHOD_SCOPED":"FAIL_AUDIT",independent_oracle:"explicit per-route arithmetic + argmin enumeration",errors,corruption_controls:mutations};
}
function auditCore(fixture,raw){const e=[];for(let i=0;i<fixture.cases.length;i++){let c=fixture.cases[i],r=raw.rows?.[i];if(!r){e.push("missing");continue}let a=c.routes.map(x=>({id:x.id,cost:x.cost})),z=c.routes.map(x=>({id:x.id,cost:x.cost+c.delta[x.id]})),p=argmin(a),q=argmin(z),same=JSON.stringify(p)===JSON.stringify(q),s=same?"FIXED_TOPOLOGY":"NONSTATIONARY_INTERVENTION",d=same?Math.min(...a.map(x=>x.cost))-Math.min(...z.map(x=>x.cost)):null;if(r.status!==s||r.endpoint_delta!==d||JSON.stringify(r.before?.selected)!==JSON.stringify(p)||JSON.stringify(r.after?.selected)!==JSON.stringify(q))e.push(c.id)}return e}
