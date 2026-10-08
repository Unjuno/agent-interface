-- Scenario setup and read-only oracle, never an agent action channel.
core.register_node("bench:stone", {description="Pad", tiles={"bench_stone.png"}, groups={cracky=1}})
core.register_node("bench:block", {description="Target block", tiles={"bench_block.png"}, groups={crumbly=1}})
local ready = false
core.set_timeofday(0.5)
local function report(label)
    local count = 0
    for x=1,3 do
        if core.get_node({x=x,y=1,z=0}).name == "bench:block" then count = count + 1 end
    end
    local p = core.get_player_by_name("feasibility")
    local value = {label=label, ready=ready, target_count=count, required_count=3,
                   task_success=ready and count==3, player_pos=p and p:get_pos() or nil}
    local f = assert(io.open(core.get_worldpath().."/oracle-"..label..".json", "w"))
    f:write(core.write_json(value)); f:close()
end
core.register_on_joinplayer(function(player)
    player:set_physics_override({speed=1,gravity=0})
    core.emerge_area({x=-16,y=-16,z=-16}, {x=16,y=16,z=16}, function(_, _, remaining)
        if remaining ~= 0 then return end
        for x=-8,8 do for z=-8,8 do
            core.set_node({x=x,y=0,z=z}, {name="bench:stone"})
        end end
        player:set_pos({x=0,y=2,z=4})
        player:set_look_horizontal(math.pi)
        player:set_look_vertical(0.8)
        local inv = player:get_inventory()
        inv:set_size("main", 8)
        inv:set_stack("main", 1, "bench:block 16")
        ready = true
        report("baseline")
    end)
end)
local elapsed = 0
core.register_globalstep(function(dt)
    elapsed = elapsed + dt
    if ready and elapsed > 6 then report("sample"); elapsed = -100000 end
end)
core.register_on_shutdown(function() report("final") end)
