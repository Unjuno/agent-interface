class InterfaceTask extends GSController {
    px=-1; py=-1; restored=false;
    function Start(); function Emit(stage,x,y);
    function Save() { return {x=this.px,y=this.py}; }
    function Load(version,data) {this.px=data.x;this.py=data.y;this.restored=true;}
}
function InterfaceTask::Emit(stage, x, y) {
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
    local guard="";
    // Query-only 7x6 neighborhood. Preserve baseline roads/ownership outside targets.
    for(local dy=-2;dy<=3;dy++) for(local dx=-2;dx<=4;dx++) {
        local t=GSMap.GetTileIndex(x+dx,y+dy);
        if(guard.len()>0) guard+=",";
        guard+="{\"id\":"+t+",\"road\":"+(GSRoad.IsRoadTile(t)?"true":"false")+",\"owner\":"+GSTile.GetOwner(t)+"}";
    }
    GSLog.Info("AIT {\"stage\":\""+stage+"\",\"x\":"+x+",\"y\":"+y+",\"width\":"+GSMap.GetMapSizeX()+",\"tiles\":["+tiles+"],\"edges\":["+edges+"],\"guard\":["+guard+"]}");
}
