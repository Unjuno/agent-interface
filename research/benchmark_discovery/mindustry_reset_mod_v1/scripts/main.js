// Setup-only save/load and read-only evidence. No controller action channel.
var SaveIO = Packages.mindustry.io.SaveIO;
var State = Packages.mindustry.core.GameState.State;
function report(){
    var rows=[];
    for(var y=0;y<Vars.world.height();y++){
        var row=[];
        for(var x=0;x<Vars.world.width();x++){
            var t=Vars.world.tile(x,y), b=t.build;
            row.push([t.floor().name,t.block().name,t.overlay().name,t.team().id,
                b==null?null:b.rotation]);
        }
        rows.push(row);
    }
    var core=Vars.state.rules.defaultTeam.core();
    var data={width:Vars.world.width(),height:Vars.world.height(),wave:Vars.state.wave,
        paused:Vars.state.isPaused(),core_present:core!=null,
        copper:core==null?null:core.items.get(Items.copper),tiles:rows,
        task_success:null,scope:"Paused setup projection only; no gameplay or trajectory determinism"};
    Vars.dataDirectory.child("oracle.json").writeString(JSON.stringify(data));
    Vars.dataDirectory.child("ready.txt").writeString("ready");
}
Events.run(Trigger.newGame,run(function(){
    Core.app.post(run(function(){
        Vars.state.set(State.paused);
        SaveIO.save(Vars.dataDirectory.child("canonical.msav"));
        report();
    }));
}));
Events.on(ClientLoadEvent,cons(function(){
    Time.run(60,run(function(){
        Core.settings.put("savecreate",false);
        Core.settings.put("fpscap",new java.lang.Integer(30));
        var input=Vars.dataDirectory.child("input.msav");
        if(input.exists()){
            SaveIO.load(input);
            Vars.state.set(State.paused);
            report();
        }else{
            var map=Vars.maps.loadInternalMap("default/fork");
            var rules=map.rules(); rules.waves=false;
            Vars.control.playMap(map,rules);
        }
    }));
}));
