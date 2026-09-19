class InterfaceOracle extends GSController { function Start(); function Emit(stage, x, y); }
function InterfaceOracle::Emit(stage, x, y) {
    local tiles = "";
    for(local dy=0;dy<2;dy++) for(local dx=0;dx<3;dx++) {
        local t=GSMap.GetTileIndex(x+dx,y+dy);
        if(tiles.len()>0) tiles+=",";
        tiles+="{\"id\":"+t+",\"road\":"+(GSRoad.IsRoadTile(t)?"true":"false")+",\"owner\":"+GSTile.GetOwner(t)+"}";
    }
    local edges="";
    for(local dx=0;dx<2;dx++) {
        local a=GSMap.GetTileIndex(x+dx,y), b=GSMap.GetTileIndex(x+dx+1,y);
        if(dx>0) edges+=",";
        edges+="["+a+","+b+","+(GSRoad.AreRoadTilesConnected(a,b)?"true":"false")+","+(GSRoad.AreRoadTilesConnected(b,a)?"true":"false")+"]";
    }
    GSLog.Info("AIO {\"stage\":\""+stage+"\",\"x\":"+x+",\"y\":"+y+",\"width\":"+GSMap.GetMapSizeX()+",\"tiles\":["+tiles+"],\"edges\":["+edges+"]}");
}
function InterfaceOracle::Start() {
    while(!GSCompany.IsValidCompany(0)) this.Sleep(1);
    this.Sleep(30);
    local company=GSCompanyMode(0);
    GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
    local px=-1,py=-1;
    for(local y=2;y<GSMap.GetMapSizeY()-2 && px<0;y++) {
        for(local x=2;x<GSMap.GetMapSizeX()-4 && px<0;x++) {
            local valid=true, h=GSTile.GetMinHeight(GSMap.GetTileIndex(x,y));
            for(local dy=0;dy<2;dy++) for(local dx=0;dx<3;dx++) {
                local t=GSMap.GetTileIndex(x+dx,y+dy);
                if(!GSTile.IsBuildable(t) || GSTile.GetSlope(t)!=GSTile.SLOPE_FLAT || GSTile.GetMinHeight(t)!=h) valid=false;
            }
            if(valid) {px=x;py=y;}
        }
    }
    if(px<0) {GSLog.Error("AIO_FIXTURE_ERROR no rectangle");return;}
    this.Emit("empty",px,py);
    local a=GSMap.GetTileIndex(px,py),b=GSMap.GetTileIndex(px+1,py),c=GSMap.GetTileIndex(px+2,py);
    if(!GSRoad.BuildRoad(a,b)) {GSLog.Error("AIO_FIXTURE_ERROR partial "+GSError.GetLastErrorString());return;}
    this.Emit("partial",px,py);
    if(!GSRoad.BuildRoad(b,c)) {GSLog.Error("AIO_FIXTURE_ERROR complete "+GSError.GetLastErrorString());return;}
    this.Emit("complete",px,py);
    if(!GSRoad.BuildRoad(GSMap.GetTileIndex(px,py+1),GSMap.GetTileIndex(px+2,py+1))) {GSLog.Error("AIO_FIXTURE_ERROR extra "+GSError.GetLastErrorString());return;}
    this.Emit("extra",px,py);
    GSLog.Info("AIO_DONE");
    while(true) this.Sleep(100);
}
