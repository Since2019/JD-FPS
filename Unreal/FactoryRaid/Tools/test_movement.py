"""Exercise the real Enhanced Input modifiers/action and character physics in PIE."""
import unreal as u,os,sys,time,json,traceback,math
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryVisual');u.EditorPythonScripting.set_keep_python_script_alive(True)
s=None;phase=0;elapsed=0;index=0;start=None;began=time.monotonic();report={'passed':False,'cases':[]}
cases=[(yaw,key,slot) for slot in ['primary1','primary2'] for yaw in [0,90,180,-90] for key in ['W','A','S','D','idle']]
def finish():
    open(os.path.join(T,'movement_test.json'),'w').write(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    global s,phase,elapsed,index,start,mappings
    try:
        if time.monotonic()-began>180:raise RuntimeError('Movement test timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:
            s=TacticalSession(world,p,True);s.ai_enabled=False
            # Ignore live desktop mouse deltas in this deterministic fixture only.
            # The production controller keeps normal mouse-look behavior.
            s.pc.set_ignore_look_input(True)
            ctx=u.load_asset('/Game/Input/IMC_Default');mappings={str(m.key.get_editor_property('key_name')):m for m in ctx.get_editor_property('default_key_mappings').get_editor_property('mappings')}
            report['active_contexts']={path:s.input_subsystem.has_mapping_context(u.load_asset(path)) for path in ['/Game/IMC_Default','/Game/Input/IMC_Default']}
            report['collision']={a.get_name():[{'name':c.get_name(),'profile':str(c.get_collision_profile_name()),'enabled':str(c.get_collision_enabled())} for c in a.get_components_by_class(u.PrimitiveComponent)] for a in [p,s.weapon]+s.weapon_visual.player_parts+s.optic.parts}
            # Isolated platform removes walls and enemies from the direction measurement.
            api=u.get_default_object(u.GameplayStatics);tf=u.Transform(location=u.Vector(0,0,3000))
            a=api.call_method('BeginDeferredActorSpawnFromClass',args=(world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,p,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));a=api.call_method('FinishSpawningActor',args=(a,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));a.set_actor_scale3d(u.Vector(30,30,.1));a.static_mesh_component.set_collision_profile_name('BlockAll');phase=1;elapsed=0
        yaw,key,slot=cases[index]
        if s.loot.equipment.selected!=slot:s.loot.equipment.select(slot)
        s.pc.set_control_rotation(u.Rotator(yaw=yaw));s.update(dt,{'RightMouseButton'} if slot=='primary2' else set())
        assert all(a.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION for a in s.optic.parts),'Optic collision re-enabled'
        if phase==1:
            p.character_movement.stop_movement_immediately();p.set_actor_location(u.Vector(0,0,3101),False,True)
            if elapsed>.4:start=p.get_actor_location();elapsed=0;phase=2
        elif phase==2:
            if key!='idle':
                m=mappings[key];s.input_subsystem.inject_input_vector_for_action(m.action,u.Vector(1,0,0),m.modifiers,m.triggers)
            if elapsed>.6:
                delta=p.get_actor_location()-start;r=math.radians(yaw);forward=(math.cos(r),math.sin(r));right=(-math.sin(r),math.cos(r));f=delta.x*forward[0]+delta.y*forward[1];side=delta.x*right[0]+delta.y*right[1]
                expected={'W':(1,0),'S':(-1,0),'A':(0,-1),'D':(0,1),'idle':(0,0)}[key];along=f*expected[0]+side*expected[1];cross=f*expected[1]-side*expected[0]
                ok=math.hypot(f,side)<.5 if key=='idle' else along>30 and abs(cross)<max(3,along*.03)
                report['cases'].append({'weapon':s.loot.equipment.loaded['name'],'yaw':yaw,'key':key,'forward_cm':f,'right_cm':side,'start':str(start),'end':str(p.get_actor_location()),'velocity':str(p.get_velocity()),'mode':str(p.character_movement.movement_mode),'root_motion':p.is_playing_root_motion(),'actor_yaw':p.get_actor_rotation().yaw,'last_input':str(p.get_last_movement_input_vector()),'ok':ok})
                index+=1;phase=1;elapsed=0
                if index==len(cases):report['passed']=all(x['ok'] for x in report['cases']);finish()
    except Exception:report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)
