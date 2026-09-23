// Empty player-ready fixture. Evaluation records one bounded engine projection after control closes.
var phase="loading";
function report(name){
    var rows=[];
    for(var y=48;y<=55;y++)for(var x=136;x<=149;x++){
        var t=Vars.world.tile(x,y),b=t.build;
        rows.push({x:x,y:y,block:t.block().name,team:t.team().id,
            rotation:b==null?null:b.rotation,floor:t.floor().name,overlay:t.overlay().name});
    }
    var core=Vars.state.rules.defaultTeam.core(),source=Vars.world.tile(137,51).build,u=Vars.player.unit();
    Vars.dataDirectory.child(name+".json").writeString(JSON.stringify({
        tick:Vars.state.tick,paused:Vars.state.isPaused(),tiles:rows,
        copper:core==null?null:core.items.get(Items.copper),core_x:core==null?null:core.x,core_y:core==null?null:core.y,
        source_item:source==null||source.config()==null?null:source.config().name,
        player_dead:Vars.player.dead(),unit:u==null?null:{x:u.x,y:u.y,type:u.type.name,plans:u.plans.size},task_success:null}));
}
Events.run(Trigger.update,run(function(){
    if(phase=="control" && Vars.dataDirectory.child("evaluate.txt").exists()){
        var u=Vars.player.unit();
        if(!Vars.state.isPaused() || Vars.player.dead() || u==null || u.plans.size!=0){
            phase="done";Vars.dataDirectory.child("evaluation-error.txt").writeString("paused live unit with no pending build plans required");
            Vars.dataDirectory.child("evaluated.txt").writeString("invalid");return;
        }
        report("after");phase="done";Vars.dataDirectory.child("evaluated.txt").writeString("done");
    }
}));
Events.run(Trigger.afterGameUpdate,run(function(){
    if(phase=="spawn" && !Vars.player.dead() && Vars.player.unit()!=null){
        Vars.state.set(Packages.mindustry.core.GameState.State.paused);
        report("before");phase="control";Vars.dataDirectory.child("ready.txt").writeString("player ready");
    }
}));
Events.on(ClientLoadEvent,cons(function(){
    Time.run(60,run(function(){
        Core.settings.put("savecreate",false);Core.settings.put("fpscap",new java.lang.Integer(30));
        Packages.mindustry.io.SaveIO.load(Vars.dataDirectory.child("input.msav"));
        var team=Vars.state.rules.defaultTeam;
        for(var y=48;y<=55;y++)for(var x=136;x<=143;x++){
            var t=Vars.world.tile(x,y);t.setBlock(Blocks.air);t.setFloor(Blocks.stone);t.setOverlay(Blocks.air);
        }
        Vars.world.tile(137,51).setBlock(Blocks.itemSource,team,0);
        Vars.world.tile(137,51).build.configured(null,Items.copper);
        phase="spawn";Vars.state.set(Packages.mindustry.core.GameState.State.playing);
    }));
}));
