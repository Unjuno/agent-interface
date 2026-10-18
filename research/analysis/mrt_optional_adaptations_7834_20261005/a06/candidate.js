const f=require("./fixture.json");
const rows=[];
for(const m of f.moderators){const p1=f.treatment_propensity[m];for(const a of [0,1])rows.push({m,a,prob:a===1?p1:1-p1,p1,y:f.potential_outcomes[m][String(a)]})}
function estimate(m){let tr=0,co=0;for(const r of rows.filter(x=>x.m===m)){if(r.a===1)tr+=r.prob*r.y/r.p1;else co+=r.prob*r.y/(1-r.p1)}return tr-co}
function gate(p,timing){return timing==="pre-treatment"&&Number.isFinite(p)&&p>0&&p<1?"IDENTIFIABLE":"NONIDENTIFIABLE"}
const effects=Object.fromEntries(f.moderators.map(m=>[m,estimate(m)]));
const pooled=f.moderators.reduce((s,m)=>s+f.moderator_mass[m]*effects[m],0);
const controls=f.controls.map(c=>({id:c.id,status:gate(c.p,c.timing)}));
console.log(JSON.stringify({allocation:f.allocation,rows,effects,pooled,heterogeneity:effects.M0-effects.M1,controls}));
