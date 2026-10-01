// Candidate only: benchmark-private in-process checkpoint/reset protocol.
var phase="loading", taskEpoch=1, canonicalCopper=null;
var benchPath=java.lang.System.getProperty("agent.interface.benchmarkControlDir");
var bench=benchPath==null?null:Core.files.absolute(benchPath);
function f(name){return bench.child(name);}
function report(name){
    var rows=[];
    for(var y=48;y<=55;y++)for(var x=136;x<=149;x++){
        var t=Vars.world.tile(x,y),b=t.build;
        rows.push({x:x,y:y,block:t.block().name,team:t.team().id,rotation:b==null?null:b.rotation,floor:t.floor().name,overlay:t.overlay().name});
    }
    var core=Vars.state.rules.defaultTeam.core(),source=Vars.world.tile(137,51).build,u=Vars.player.unit();
    f(name+".json").writeString(JSON.stringify({tick:Vars.state.tick,paused:Vars.state.isPaused(),tiles:rows,copper:core.items.get(Items.copper),core_x:core.x,core_y:core.y,source_item:source.config().name,player_dead:Vars.player.dead(),unit:{x:u.x,y:u.y,type:u.type.name,plans:u.plans.size}}));
}
Events.run(Trigger.update,run(function(){
    if(phase=="control" && f("checkpoint-"+taskEpoch+".request").exists()){
        var u=Vars.player.unit();
        if(!Vars.state.isPaused() || Vars.player.dead() || u==null || u.plans.size!=0){phase="failed";f("checkpoint-"+taskEpoch+".error").writeString("paused live unit with no pending plans required");return;}
        report("after-"+taskEpoch); phase="awaitReset"; f("checkpoint-"+taskEpoch+".ack").writeString("snapshot ready"); return;
    }
    if(phase=="awaitReset" && f("score-pass-"+taskEpoch+".receipt").exists() && f("reset-"+taskEpoch+".request").exists()){
        var target=Vars.world.tile(137,52),core=Vars.state.rules.defaultTeam.core();
        target.setBlock(Blocks.air); core.items.set(Items.copper,canonicalCopper);
        report("reset-"+taskEpoch); f("reset-"+taskEpoch+".ack").writeString("reset witness ready");
        taskEpoch++; phase=taskEpoch<=6?"control":"done";
        if(taskEpoch<=6)f("ready-"+taskEpoch+".ack").writeString("next task ready");
    }
    if(phase=="awaitReset" && f("score-fail-"+taskEpoch+".receipt").exists()){phase="failed";f("failed-"+taskEpoch+".ack").writeString("task failed; reset forbidden");}
}));
Events.run(Trigger.afterGameUpdate,run(function(){
    if(phase=="spawn" && !Vars.player.dead() && Vars.player.unit()!=null){
        Vars.state.set(Packages.mindustry.core.GameState.State.paused);
        canonicalCopper=Vars.state.rules.defaultTeam.core().items.get(Items.copper);
        report("before-1"); phase="control"; f("ready-1.ack").writeString("task ready");
    }
}));
