import unreal as u,os,sys,time,json,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession
from loot_model import item,insert,move
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker')
s=None;phase=0;elapsed=0.;started=time.monotonic();report={'passed':False}
def finish():
    open(os.path.join(T,'equipment_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    global s,phase,elapsed
    try:
        if time.monotonic()-started>140:raise RuntimeError('timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:
            if elapsed<3:return
            s=TacticalSession(world,p,True);s.ai_enabled=False;elapsed=0
        s.update(dt,set())
        e=s.loot.equipment
        if phase==1 and elapsed>2:
            helmet=item('FAST 风格头盔');rifle=item('MK18 风格步枪');rifle['ammo']=7
            assert insert(s.pack,helmet) and insert(s.pack,rifle)
            s.loot.open();phase=2;elapsed=0
        elif phase==2 and elapsed>.5:
            report['pointer']=[e.pointer().x,e.pointer().y]
            helmet=next(i for i in s.pack if i['name']=='FAST 风格头盔')
            start=u.Vector2D(48+helmet['x']*86+137,282+helmet['y']*62+99)
            e.begin('Pack',s.pack.index(helmet),start)
            original_pointer=e.pointer;cursor=start+u.Vector2D(37,23);e.pointer=lambda:cursor
            e.update(set());ghost=e.ghost.get_editor_property('slot').get_position()
            assert abs(ghost.x-(48+helmet['x']*86+37))<.01 and abs(ghost.y-(282+helmet['y']*62+23))<.01
            report['pixel_grab_anchor']=True;e.cancel();e.pointer=original_pointer
            e.begin('Pack',s.pack.index(helmet),u.Vector2D(49+helmet['x']*86,283+helmet['y']*62));e.release(u.Vector2D(70,175))
            assert e.slots['head'] is helmet and len(e.helmet_parts)==4 and helmet not in s.pack
            rifle=next(i for i in s.pack if i['kind']=='WEAPON')
            e.begin('Pack',s.pack.index(rifle),u.Vector2D(49+rifle['x']*86,283+rifle['y']*62));e.release(u.Vector2D(450,175))
            assert e.slots['primary2'] is rifle
            s.loot.close();s.update(.01,{'Two'});assert e.loaded is rifle and s.prop(s.weapon,'Current Bullets')==7
            s.weapon.set_editor_property('Current Bullets',5);s.update(.01,set());s.update(.01,{'One'});assert s.prop(s.weapon,'Current Bullets')!=5
            s.update(.01,set());s.update(.01,{'Two'});assert s.prop(s.weapon,'Current Bullets')==5
            report['independent_ammo']=True;s.loot.open();phase=3;elapsed=0
        elif phase==3 and elapsed>.5:
            helmet=e.slots['head'];e.begin('head',0,u.Vector2D(70,175));e.release(u.Vector2D(49,283+62*2))
            assert e.slots['head'] is None and helmet in s.pack and len(e.helmet_parts)==0
            e.begin('Pack',s.pack.index(helmet),u.Vector2D(49+helmet['x']*86,283+helmet['y']*62));e.release(u.Vector2D(450,175))
            assert helmet in s.pack and e.slots['primary2']['kind']=='WEAPON'
            e.begin('Pack',s.pack.index(helmet),u.Vector2D(49+helmet['x']*86,283+helmet['y']*62));e.release(u.Vector2D(70,175))
            report['helmet_equip_unequip']=True;report['invalid_drop_preserved']=True
            s.loot.draw();u.SystemLibrary.execute_console_command(world,'Shot showui filename="'+os.path.join(T,'equipment_ui.png').replace('\\','/')+'"');phase=4;elapsed=0
        elif phase==4 and elapsed>1:
            assert move(e.slots,'primary2',s.pack,e.slots['primary2']);e.sync();assert e.loaded is None
            s.loot.close();s.update(.01,{'LeftMouseButton','RightMouseButton'});assert not s.trigger_active
            report['empty_slot_blocks_fire']=True;phase=5;elapsed=0
        elif phase==5 and elapsed>.5:
            assert s.stance.set('crouch');phase=6;elapsed=0
        elif phase==6 and elapsed>.7:
            assert s.stance.mode=='crouch' and s.player.character_movement.max_walk_speed==125
            report['crouch_eye']=s.stance.eye;assert abs(s.stance.eye-100)<2
            assert s.stance.set('prone');phase=7;elapsed=0
        elif phase==7 and elapsed>.7:
            report['prone_eye']=s.stance.eye;assert abs(s.stance.eye-43)<2
            assert s.player.character_movement.max_walk_speed==65
            assert s.player.capsule_component.get_unscaled_capsule_half_height()==24
            api=u.get_default_object(u.GameplayStatics);tf=u.Transform()
            ceiling=api.call_method('BeginDeferredActorSpawnFromClass',args=(world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            ceiling=api.call_method('FinishSpawningActor',args=(ceiling,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            c=ceiling.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));c.set_collision_profile_name('BlockAll')
            ceiling.set_actor_scale3d(u.Vector(3,3,.2));ceiling.set_actor_location(p.get_actor_location()+u.Vector(0,0,70),False,True)
            assert not s.stance.set('stand'),'Ceiling must block standing up'
            ceiling.destroy_actor();report['ceiling_blocks_stand']=True
            assert s.stance.set('stand');phase=8;elapsed=0
        elif phase==8 and elapsed>.7:
            assert abs(s.stance.eye-s.stance.stand_eye)<2
            report['stance_cycle']=True;report['passed']=True;finish()
    except Exception:report['error']=traceback.format_exc();u.log_error(report['error']);finish()
handle=u.register_slate_post_tick_callback(tick)
