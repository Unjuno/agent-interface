// Setup-only API access and read-only oracle. No action selection channel.
function report(label){
    var rows = [];
    for(var y=0; y<Vars.world.height(); y++){
        var row=[];
        for(var x=0; x<Vars.world.width(); x++){
            var t=Vars.world.tile(x,y);
            row.push([t.floor().name,t.block().name,t.overlay().name,t.team().id,t.rotation]);
        }
        rows.push(row);
    }
    var core=Vars.state.rules.defaultTeam.core();
    var data={label:label,map:Vars.state.map.name(),width:Vars.world.width(),height:Vars.world.height(),
        wave:Vars.state.wave,core_present:core!=null,copper:core==null?null:core.items.get(Items.copper),
        tiles:rows,task_success:null,scope:"No agent actions; initial-state/scoring feasibility only"};
    Vars.dataDirectory.child("oracle-"+label+".json").writeString(JSON.stringify(data));
}
Events.run(Trigger.newGame,run(function(){
    report("baseline");
    Time.run(180,run(function(){report("sample");}));
}));
Events.on(ClientLoadEvent,cons(function(){
    Time.run(60,run(function(){
        Core.settings.put("savecreate",false);
        Core.settings.put("fpscap",30);
        var map=Vars.maps.loadInternalMap("default/fork");
        var rules=map.rules();
        rules.waves=false;
        Vars.control.playMap(map,rules);
    }));
}));
