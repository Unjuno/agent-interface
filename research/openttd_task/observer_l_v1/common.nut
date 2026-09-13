class InterfaceTask extends GSController {
    px=-1; py=-1; restored=false;
    function Start(); function Emit(stage,x,y);
    function Save() { return {x=this.px,y=this.py}; }
    function Load(version,data) {this.px=data.x;this.py=data.y;this.restored=true;}
}
function InterfaceTask::Emit(stage, x, y) {
    local w=GSMap.GetMapSizeX();
    local target=[GSMap.GetTileIndex(x,y),GSMap.GetTileIndex(x+1,y),GSMap.GetTileIndex(x+2,y),GSMap.GetTileIndex(x+2,y+1),GSMap.GetTileIndex(x+2,y+2)];
    local forbidden=[GSMap.GetTileIndex(x,y+1),GSMap.GetTileIndex(x+1,y+1),GSMap.GetTileIndex(x,y+2),GSMap.GetTileIndex(x+1,y+2)];
    local tiles="";
    foreach(t in target) {if(tiles.len()>0) tiles+=",";tiles+="{\"id\":"+t+",\"road\":"+(GSRoad.IsRoadTile(t)?"true":"false")+",\"owner\":"+GSTile.GetOwner(t)+"}";}
    foreach(t in forbidden) {if(tiles.len()>0) tiles+=",";tiles+="{\"id\":"+t+",\"road\":"+(GSRoad.IsRoadTile(t)?"true":"false")+",\"owner\":"+GSTile.GetOwner(t)+"}";}
    local edges="";
    for(local i=0;i<target.len()-1;i++) {local a=target[i],b=target[i+1];if(edges.len()>0) edges+=",";edges+="["+a+","+b+","+(GSRoad.AreRoadTilesConnected(a,b)?"true":"false")+","+(GSRoad.AreRoadTilesConnected(b,a)?"true":"false")+"]";}
    local guard="";
    for(local dy=-2;dy<=4;dy++) for(local dx=-2;dx<=4;dx++) {local t=GSMap.GetTileIndex(x+dx,y+dy);if(guard.len()>0) guard+=",";guard+="{\"id\":"+t+",\"road\":"+(GSRoad.IsRoadTile(t)?"true":"false")+",\"owner\":"+GSTile.GetOwner(t)+"}";}
    GSLog.Info("AIT {\"stage\":\""+stage+"\",\"x\":"+x+",\"y\":"+y+",\"width\":"+w+",\"tiles\":["+tiles+"],\"edges\":["+edges+"],\"guard\":["+guard+"]}");
}
