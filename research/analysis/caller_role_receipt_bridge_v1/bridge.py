import copy

FOCUS_BLOB="8557cc1a70487df7abbfffb965a9e4d38ac3bfd5"
TARGET_BLOB="78cfc40ce061f89c870ec1afc2bc724c391bd4cd"
REUSABLE="PREPARED_REUSABLE_VERSIONED"
FRESH="FRESH_COMMIT_BOUND_CURRENT"

class RoleReceiptBridge:
    def __init__(self):
        self.persistent=[]
        self.consumed=set()
        self.rejections=[]

    def store(self, receipt):
        if type(receipt) is not dict:
            self.rejections.append("malformed")
            return False
        role=receipt.get("role")
        if role!=REUSABLE:
            self.rejections.append("nonreusable_role")
            return False
        if receipt.get("storage")!="PERSIST_DEPENDENCY":
            self.rejections.append("bad_reusable_storage")
            return False
        if receipt.get("scope")!="FOCUS_OBSERVATION_CURRENTNESS" or receipt.get("source_blob")!=FOCUS_BLOB:
            self.rejections.append("bad_reusable_source")
            return False
        self.persistent=[copy.deepcopy(receipt)]
        return True

    def reusable_current(self):
        if len(self.persistent)!=1:
            return False
        r=self.persistent[0]
        return r.get("current") is True and r.get("role")==REUSABLE and r.get("storage")=="PERSIST_DEPENDENCY"

    def bind_gate(self, receipt, intent_id, commit_epoch):
        if type(receipt) is not dict:
            return None
        if receipt.get("role")!=FRESH or receipt.get("storage")!="EPHEMERAL_ONLY":
            self.rejections.append("bad_gate_role_or_storage")
            return None
        if receipt.get("scope")!="TARGET_HANDLE_CURRENTNESS" or receipt.get("source_blob")!=TARGET_BLOB:
            self.rejections.append("bad_gate_source")
            return None
        env=copy.deepcopy(receipt)
        env["intent_id"]=intent_id
        env["commit_epoch"]=commit_epoch
        env["token"]=f"{intent_id}:{commit_epoch}:{receipt.get('lineage')}"
        return env

    def reuse_revalidate(self, payload):
        if self.reusable_current():
            return {"status":"revalidated","target":copy.deepcopy(payload)}
        return {"status":"stale"}

    def final_revalidate(self, payload, gate, intent_id, commit_epoch):
        if gate is None:
            return {"status":"missing"}
        token=gate.get("token")
        if token in self.consumed:
            return {"status":"stale"}
        if gate.get("role")!=FRESH or gate.get("storage")!="EPHEMERAL_ONLY":
            return {"status":"stale"}
        if gate.get("intent_id")!=intent_id or gate.get("commit_epoch")!=commit_epoch:
            return {"status":"stale"}
        if gate.get("lineage_current") is not True:
            return {"status":"stale"}
        truth=gate.get("truth")
        self.consumed.add(token)
        if truth!="TRUE":
            return {"status":"missing" if truth=="FALSE" else "stale"}
        return {"status":"revalidated","target":copy.deepcopy(payload)}
