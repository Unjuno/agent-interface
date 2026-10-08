const argmin = rows => { const m = Math.min(...rows.map(x => x.cost)); return rows.filter(x => x.cost === m).map(x => x.id).sort(); };
export function evaluate(fixture) {
 return {schema:"route-selector-explicit-5911-candidate-v1",selector:fixture.selector,tie_policy:fixture.tie_policy,rows:fixture.cases.map(c=>{
  const before=c.routes.map(x=>({id:x.id,cost:x.cost}));
  const after=c.routes.map(x=>({id:x.id,cost:x.cost+c.delta[x.id]}));
  const pre=argmin(before),post=argmin(after),same=JSON.stringify(pre)===JSON.stringify(post);
  return {case_id:c.id,before:{routes:before,selected:pre,endpoint_cost:Math.min(...before.map(x=>x.cost))},after:{routes:after,selected:post,endpoint_cost:Math.min(...after.map(x=>x.cost))},status:same?"FIXED_TOPOLOGY":"NONSTATIONARY_INTERVENTION",endpoint_delta:same?Math.min(...before.map(x=>x.cost))-Math.min(...after.map(x=>x.cost)):null};
 })};
}
