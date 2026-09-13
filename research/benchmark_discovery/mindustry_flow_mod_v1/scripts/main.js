// Fixture creation and read-only snapshots for score calibration, not agent actions.
var active=false,startTick=0;
function report(name){
    var rows=[];
    for(var y=48;y<=55;y++)for(var x=136;x<=149;x++){
        var t=Vars.world.tile(x,y),b=t.build;
        rows.push({x:x,y:y,block:t.block().name,team:t.team().id,
            rotation:b==null?null:b.rotation,floor:t.floor().name,overlay:t.overlay().name});
    }
    var core=Vars.state.rules.defaultTeam.core();
    var source=Vars.world.tile(137,51).build;
    Vars.dataDirectory.child(name+".json").writeString(JSON.stringify({
        tick:Vars.state.tick,paused:Vars.state.isPaused(),tiles:rows,
        copper:core.items.get(Items.copper),core_x:core.x,core_y:core.y,
        source_item:source.config()==null?null:source.config().name,task_success:null}));
}
Events.run(Trigger.afterGameUpdate,run(function(){
    if(active && Vars.state.tick-startTick>=600){
        active=false;Vars.state.set(Packages.mindustry.core.GameState.State.paused);
        report("after");Vars.dataDirectory.child("ready.txt").writeString("done");
    }
}));
Events.on(ClientLoadEvent,cons(function(){
    Time.run(60,run(function(){
        Core.settings.put("savecreate",false);
        Core.settings.put("fpscap",new java.lang.Integer(30));
        Packages.mindustry.io.SaveIO.load(Vars.dataDirectory.child("input.msav"));
        Vars.state.set(Packages.mindustry.core.GameState.State.paused);
        var team=Vars.state.rules.defaultTeam;
        // Clear a small west-of-core area while retaining the receiving core.
        for(var y=48;y<=55;y++)for(var x=136;x<=143;x++){
            var t=Vars.world.tile(x,y);t.setBlock(Blocks.air);
            t.setFloor(Blocks.stone);t.setOverlay(Blocks.air);
        }
        Vars.world.tile(137,51).setBlock(Blocks.itemSource,team,0);
        Vars.world.tile(137,51).build.configured(null,Items.copper);
        report("before");
        var variant=Vars.dataDirectory.child("variant.txt").readString().trim();
        for(var x=138;x<=143;x++){
            if(variant=="empty" || (variant=="missing" && x==140) || (variant=="partial" && x>=141))continue;
            Vars.world.tile(x,51).setBlock(Blocks.conveyor,team,variant=="reversed" && x==140?2:0);
        }
        if(variant=="extra")Vars.world.tile(140,50).setBlock(Blocks.conveyor,team,0);
        report("constructed");
        startTick=Vars.state.tick;active=true;
        Vars.state.set(Packages.mindustry.core.GameState.State.playing);
    }));
}));
