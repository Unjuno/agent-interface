// Load pinned fixture once. Subsequent samples are read-only, never control.
var loaded=false, last=0, count=0;
function sample(){
    var p=Vars.player, u=p.unit(), core=p.team().core();
    var data={sample:count++,paused:Vars.state.isPaused(),tick:Vars.state.tick,
        player_dead:p.dead(),player_x:p.x,player_y:p.y,
        unit:u==null?null:{id:u.id,type:u.type.name,x:u.x,y:u.y,dead:u.dead,added:u.isAdded()},
        core:core==null?null:{x:core.x,y:core.y,copper:core.items.get(Items.copper)},
        camera:{x:Core.camera.position.x,y:Core.camera.position.y},
        task_success:null};
    Vars.dataDirectory.child("readiness.jsonl").writeString(JSON.stringify(data)+"\n",true);
}
Events.run(Trigger.update,run(function(){
    if(!loaded)return;
    var now=java.lang.System.currentTimeMillis();
    if(now-last>=100){last=now;sample();}
}));
Events.on(ClientLoadEvent,cons(function(){
    Time.run(60,run(function(){
        Core.settings.put("savecreate",false);
        Core.settings.put("fpscap",new java.lang.Integer(30));
        Packages.mindustry.io.SaveIO.load(Vars.dataDirectory.child("input.msav"));
        Vars.state.set(Packages.mindustry.core.GameState.State.paused);
        loaded=true;sample();
        Vars.dataDirectory.child("ready.txt").writeString("ready");
    }));
}));
