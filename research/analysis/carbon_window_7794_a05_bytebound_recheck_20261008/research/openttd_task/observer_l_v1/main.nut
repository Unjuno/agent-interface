require("common.nut");
function InterfaceTask::Start() {
    if(!this.restored || this.px<0 || this.py<0) {GSLog.Error("AIT_ERROR saved contract required");return;}
    local company=GSCompanyMode(0);
    GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
    this.Emit("restored",this.px,this.py);
    GSLog.Info("AIT_READY");
    while(true){this.Sleep(30);this.Emit("observe",this.px,this.py);}
}
