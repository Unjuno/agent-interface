require("common.nut");
function InterfaceTask::Start() {
    while(GSCompany.ResolveCompanyID(0)!=0) this.Sleep(1);
    this.Sleep(30);
    local company=GSCompanyMode(0);
    GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
    for(local y=2;y<GSMap.GetMapSizeY()-7 && this.px<0;y++) {
        for(local x=2;x<GSMap.GetMapSizeX()-10 && this.px<0;x++) {
            local valid=true,h=GSTile.GetMinHeight(GSMap.GetTileIndex(x,y));
            for(local dy=0;dy<2;dy++) for(local dx=0;dx<3;dx++) {
                local t=GSMap.GetTileIndex(x+dx,y+dy);
                if(!GSTile.IsBuildable(t) || GSTile.GetSlope(t)!=GSTile.SLOPE_FLAT || GSTile.GetMinHeight(t)!=h) valid=false;
            }
            if(valid){this.px=x;this.py=y;}
        }
    }
    if(this.px<0){GSLog.Error("AIT_ERROR no rectangle");return;}
    GSSign.BuildSign(GSMap.GetTileIndex(this.px,this.py),"A");
    GSSign.BuildSign(GSMap.GetTileIndex(this.px+2,this.py),"C");
    GSSign.BuildSign(GSMap.GetTileIndex(this.px+1,this.py+1),"X forbidden row");
    GSViewport.ScrollCompanyClientsTo(0,GSMap.GetTileIndex(this.px+1,this.py));
    this.Emit("setup",this.px,this.py);
    GSLog.Info("AIT_READY");
    while(true) this.Sleep(100);
}


