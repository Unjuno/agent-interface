import copy
FOCUS_BLOB="8557cc1a70487df7abbfffb965a9e4d38ac3bfd5"
REUSABLE="PREPARED_REUSABLE_VERSIONED"
FRESH="FRESH_COMMIT_BOUND_CURRENT"

class ReusableReceiptStore:
    def __init__(self):
        self.rows={}
        self.rejections=[]

    def store(self, receipt):
        if type(receipt) is not dict:
            self.rejections.append("malformed"); return False
        if receipt.get("role")!=REUSABLE:
            self.rejections.append("nonreusable_role"); return False
        if receipt.get("storage")!="PERSIST_DEPENDENCY":
            self.rejections.append("bad_storage"); return False
        if receipt.get("scope")!="FOCUS_OBSERVATION_CURRENTNESS":
            self.rejections.append("bad_scope"); return False
        if receipt.get("source_blob")!=FOCUS_BLOB:
            self.rejections.append("bad_source"); return False
        sid=receipt.get("session_id"); resource=receipt.get("canonical_resource")
        if type(sid) is not str or not sid:
            self.rejections.append("missing_session"); return False
        if type(resource) is not str or not resource:
            self.rejections.append("missing_resource"); return False
        self.rows[(sid,resource)]=copy.deepcopy(receipt)
        return True

    def revalidate(self, session_id, canonical_resource, payload):
        row=self.rows.get((session_id,canonical_resource))
        if row is None:
            return {"status":"stale"}
        if row.get("current") is not True:
            return {"status":"stale"}
        return {"status":"revalidated","target":copy.deepcopy(payload)}

    def persistent_commit_count(self):
        return sum(x.get("role")==FRESH for x in self.rows.values())
