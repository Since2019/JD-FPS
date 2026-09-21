import unreal as u
import time, json, os, traceback
u.EditorPythonScripting.set_keep_python_script_alive(True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
level.load_level('/Game/Factory/Maps/ClassicFactoryArmed')
started=time.monotonic()
result_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'weapon_test.json')
phase=0
report={}
weapon=None

def finish():
    open(result_path,'w',encoding='utf-8').write(json.dumps(report,indent=2))
    u.unregister_slate_post_tick_callback(callback)
    level.editor_request_end_play()
    u.EditorPythonScripting.set_keep_python_script_alive(False)

def tick(dt):
    global phase,weapon,started
    try:
        elapsed=time.monotonic()-started
        if elapsed>90:raise RuntimeError('PIE test timeout')
        if phase==0:
            level.editor_request_begin_play();phase=1;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        player=u.GameplayStatics.get_player_character(world,0)
        if not player:return
        if phase==1 and elapsed>5:
            report['pawn']=player.get_class().get_name()
            report['player_location']=str(player.get_actor_location())
            report['pickups']=[]
            for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor):
                if 'Pickup' in a.get_class().get_name():
                    props={'location':str(a.get_actor_location()),'class':a.get_class().get_name()}
                    for k in ['Weapon Type','Weapon Class']:
                        try:props[k]=str(a.get_editor_property(k))
                        except Exception:pass
                    props['components']=[{'name':c.get_name(),'location':str(c.get_world_location()),'overlap':c.get_editor_property('generate_overlap_events'),'collision':str(c.get_collision_enabled()),'pawn_response':str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN))} for c in a.get_components_by_class(u.PrimitiveComponent)]
                    report['pickups'].append(props)
            weapon=player.get_editor_property('Current Weapon')
            if not weapon:raise RuntimeError('Player did not automatically equip the starting rifle')
            report['weapon']=weapon.get_class().get_name()
            report['ammo_before']=weapon.get_editor_property('Current Bullets')
            weapon.call_method('Start Firing')
            started=time.monotonic();phase=2
        elif phase==2 and elapsed>1:
            weapon.call_method('Stop Firing')
            report['ammo_after']=weapon.get_editor_property('Current Bullets')
            assert report['ammo_after']<report['ammo_before'],'Firing did not consume ammunition'
            report['passed']=True
            finish()
    except Exception:
        report['passed']=False;report['error']=traceback.format_exc();finish()

callback=u.register_slate_post_tick_callback(tick)
