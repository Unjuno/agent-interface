class InterfaceFeasibility extends GSController {
    function Start();
}
function InterfaceFeasibility::Start() {
    local width = GSMap.GetMapSizeX();
    local height = GSMap.GetMapSizeY();
    // Emit read-only initial terrain/road state for independent reset auditing.
    for (local y = 0; y < height; y++) {
        local row = "";
        for (local x = 0; x < width; x++) {
            local t = GSMap.GetTileIndex(x,y);
            row += GSTile.GetMinHeight(t) + ":" + GSTile.GetOwner(t) + ":" +
                (GSTile.HasTransportType(t,GSTile.TRANSPORT_ROAD) ? "1" : "0") + ",";
        }
        GSLog.Info("AIFS_ROW " + y + " " + row);
    }
    GSLog.Info("AIFS_READY " + width + " " + height);
    while (true) {
        local count = 0;
        for (local x = 10; x < 13; x++) {
            local t = GSMap.GetTileIndex(x,10);
            if (GSTile.HasTransportType(t,GSTile.TRANSPORT_ROAD) && GSTile.GetOwner(t)==0) count++;
        }
        GSLog.Info("AIFS_TARGET_OWNED_ROAD_COUNT " + count);
        this.Sleep(30);
    }
}
