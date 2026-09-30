// Deterministic held-out compositional safety-filter study for Issue #5317 T3.
(studySourceSha256, auditSourceSha256) => {
  const ACTIONS = ["SIGN", "PUBLISH", "INDEX", "HASH", "REVOKE", "ACTIVATE", "ARCHIVE", "NOTIFY"];
  const RISK = {SIGN:2, PUBLISH:4, INDEX:2, HASH:3, REVOKE:5, ACTIVATE:3, ARCHIVE:3, NOTIFY:1};
  const UTILITY = {SIGN:4, PUBLISH:5, INDEX:3, HASH:2, REVOKE:4, ACTIVATE:4, ARCHIVE:2, NOTIFY:1};
  const BUDGET = 10;
  const RULES = {
    order: {id:"order", type:"before", first:"SIGN", second:"PUBLISH"},
    requires: {id:"requires", type:"requires", action:"INDEX", required:"HASH"},
    mutex: {id:"mutex", type:"mutex", left:"REVOKE", right:"ACTIVATE"}
  };
  const CONTRACTS = [
    ["order","requires"], ["order","mutex"], ["requires","mutex"], ["order","requires","mutex"]
  ];
  function hasViolation(prefix, rules) {
    const seen = new Set();
    for (const action of prefix) {
      for (const rule of rules) {
        if (rule.type === "before" && action === rule.second && !seen.has(rule.first)) return true;
        if (rule.type === "requires" && action === rule.action && !seen.has(rule.required)) return true;
        if (rule.type === "mutex" &&
            ((action === rule.left && seen.has(rule.right)) ||
             (action === rule.right && seen.has(rule.left)))) return true;
      }
      seen.add(action);
    }
    return false;
  }
  function filter(sequence, rules, semantic) {
    const accepted = [];
    let risk = 0, checks = 0, reason = "COMPLETE";
    for (const action of sequence) {
      checks++;
      if (risk + RISK[action] > BUDGET) { reason = "BUDGET"; break; }
      if (semantic && hasViolation(accepted.concat(action), rules)) {
        reason = "UNSAFE_PREFIX";
        break;
      }
      accepted.push(action);
      risk += RISK[action];
    }
    return {accepted, checks, reason};
  }
  function stable(value) {
    if (Array.isArray(value)) return "[" + value.map(stable).join(",") + "]";
    if (value && typeof value === "object")
      return "{" + Object.keys(value).sort().map(k => JSON.stringify(k)+":"+stable(value[k])).join(",") + "}";
    return JSON.stringify(value);
  }
  let hash = 14695981039346656037n;
  const prime = 1099511628211n, mask = (1n << 64n) - 1n;
  function digest(text) {
    for (let i=0;i<text.length;i++) { hash ^= BigInt(text.charCodeAt(i)); hash = (hash * prime) & mask; }
  }
  function zeroArm() {
    return {admittedActions:0, utility:0, risk:0, casesWithUnsafePrefix:0,
      unsafeAdmittedPrefixes:0, fullSafeProposals:0, completedSafeProposals:0,
      falseBlocks:0, prefixChecks:0, budgetStops:0, unsafeStops:0};
  }
  const arms = {risk_only_prefix:zeroArm(), semantic_prefix:zeroArm()};
  let cases=0, sequences=0;
  function walk(prefix, rules, contractId) {
    if (prefix.length === 4) {
      sequences++;
      const baseline=filter(prefix,rules,false), candidate=filter(prefix,rules,true);
      const safeWhole=!hasViolation(prefix,rules);
      const withinBudget=prefix.reduce((n,a)=>n+RISK[a],0)<=BUDGET;
      const fullSafe=safeWhole && withinBudget;
      const unsafeCount=Array.from({length:baseline.accepted.length},(_,i)=>i+1)
        .filter(n=>hasViolation(baseline.accepted.slice(0,n),rules)).length;
      const b=arms.risk_only_prefix, s=arms.semantic_prefix;
      for (const [arm,result,isSemantic] of [[b,baseline,false],[s,candidate,true]]) {
        arm.admittedActions+=result.accepted.length;
        arm.utility+=result.accepted.reduce((n,a)=>n+UTILITY[a],0);
        arm.risk+=result.accepted.reduce((n,a)=>n+RISK[a],0);
        arm.prefixChecks+=result.checks;
        if (result.reason==="BUDGET") arm.budgetStops++;
        if (result.reason==="UNSAFE_PREFIX") arm.unsafeStops++;
        if (!isSemantic && unsafeCount>0) arm.casesWithUnsafePrefix++;
        if (!isSemantic) arm.unsafeAdmittedPrefixes+=unsafeCount;
        if (fullSafe) {
          arm.fullSafeProposals++;
          if (result.accepted.length===prefix.length) arm.completedSafeProposals++;
          else arm.falseBlocks++;
        }
      }
      digest(contractId+"|"+prefix.join(",")+"|"+baseline.accepted.join(",")+"|"+
        candidate.accepted.join(",")+"|"+(safeWhole?"1":"0")+"|"+(withinBudget?"1":"0")+";");
      cases++;
      return;
    }
    for (const action of ACTIONS) walk(prefix.concat(action),rules,contractId);
  }
  for (const names of CONTRACTS) {
    const rules=names.map(name=>RULES[name]);
    walk([],rules,names.join("+"));
  }
  const primitiveControls=[
    hasViolation(["PUBLISH"],[RULES.order])===true,
    hasViolation(["SIGN","PUBLISH"],[RULES.order])===false,
    hasViolation(["INDEX"],[RULES.requires])===true,
    hasViolation(["HASH","INDEX"],[RULES.requires])===false,
    hasViolation(["REVOKE","ACTIVATE"],[RULES.mutex])===true,
    hasViolation(["REVOKE"],[RULES.mutex])===false
  ];
  const unknownContract={schema:99,rules:Object.values(RULES)};
  const malformedContract={schema:1,rules:[{id:"bad",type:"unmodeled",action:"SIGN"}]};
  function failClosed(contract) {
    if (contract.schema!==1 || contract.rules.some(r=>!["before","requires","mutex"].includes(r.type)))
      return {status:"UNKNOWN",accepted:[]};
    return {status:"KNOWN",accepted:["SIGN"]};
  }
  const unknown=failClosed(unknownContract), malformed=failClosed(malformedContract);
  const result={
    status:"RUNNER_COMPLETE", study_source_sha256:studySourceSha256, audit_source_sha256:auditSourceSha256,
    runtime:"Codex functions.exec V8 isolate; deterministic, in-memory",
    actions:ACTIONS, risk_budget:BUDGET, contracts:CONTRACTS, contract_count:CONTRACTS.length,
    sequences_per_contract:Math.pow(ACTIONS.length,4), cases, sequences,
    arms,
    controls:{primitive_predicate_controls_passed:primitiveControls.filter(Boolean).length, primitive_predicate_controls_total:primitiveControls.length, unknown_contract_status:unknown.status, unknown_contract_actions:unknown.accepted.length,
      malformed_contract_status:malformed.status, malformed_contract_actions:malformed.accepted.length},
    case_digest_fnv1a64:hash.toString(16).padStart(16,"0"),
    scope:"synthetic finite-state prefix filtering only; no runtime or external-task evidence"
  };
  return result;
}
