import unreal as u,os,sys,time,json,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker')
s=None;phase=0;elapsed=0.;started=time.monotonic();capture=None;report={'passed':False}
def finish():
    open(os.path.join(T,'icebreaker_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
    u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(name):
    global capture
    if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,os.path.join(T,'icebreaker_'+name+'.png'))
    if capture and capture.is_task_done():capture=None;return True
    return False
def place(pos,rot):
    s.player.character_movement.stop_movement_immediately();s.player.set_actor_location(u.Vector(*pos),False,True);s.pc.set_control_rotation(u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]))
def tick(dt):
    global s,phase,elapsed
    try:
        if time.monotonic()-started>200:raise RuntimeError('Icebreaker test timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:
            if elapsed<3:return
            s=TacticalSession(world,p,True);s.ai_enabled=False;elapsed=0
        keys={'RightMouseButton'} if phase==5 else {'F'} if phase==9 else {'LeftMouseButton'} if phase==10 else set()
        s.update(dt,keys)
        if phase==1 and elapsed>4 and shot('deck'):
            report['enemies']=len(s.enemies);report['containers']=len(s.boxes);assert len(s.enemies)==6 and len(s.boxes)==6
            report['spawn_z']=p.get_actor_location().z;assert 80<p.get_actor_location().z<120,'Deck collision failed'
            assert len(s.weapon_visual.applied)==7
            place((-1380,0,98),(0,0,0));phase=2;elapsed=0
        elif phase==2 and elapsed>3 and shot('engine'):
            assert 80<p.get_actor_location().z<120
            place((-1190,-690,98),(0,0,0));phase=3;elapsed=0
        elif phase==3:
            if elapsed<3.4:p.add_movement_input(u.Vector(1,0,0),1,True)
            else:
                report['stairs_position']=str(p.get_actor_location());assert p.get_actor_location().z>440,'Could not walk up bridge stairs'
                p.character_movement.stop_movement_immediately();phase=7;elapsed=0
        elif phase==7:
            if elapsed<2.4:p.add_movement_input(u.Vector(0,1,0),1,True)
            else:
                assert p.get_actor_location().y>-100,'Upper railing blocks stair landing'
                p.character_movement.stop_movement_immediately();phase=8;elapsed=0
        elif phase==8:
            if elapsed<1.2:p.add_movement_input(u.Vector(1,0,0),1,True)
            else:
                assert p.get_actor_location().x>0,'Cannot enter bridge from upper deck'
                report['walked_from_deck_into_bridge']=True
                p.character_movement.stop_movement_immediately();phase=4;elapsed=0
        elif phase==4 and elapsed>3 and shot('bridge'):
            assert 440<p.get_actor_location().z<480,'Bridge floor collision failed'
            phase=5;elapsed=0
        elif phase==5 and elapsed>1.5 and shot('ads'):
            assert s.ads>.99 and s.aim_error<.15;report['ads_error_cm']=s.aim_error
            place((-3640,-210,98),(-34,0,0));phase=9;elapsed=0
        elif phase==9 and elapsed>2.8:
            assert any(b['searched'] for b in s.boxes),'Deck search case not accessible'
            report['searched_container']=True;report['ammo_before']=prop(s.weapon,'Current Bullets');phase=10;elapsed=0
        elif phase==10 and elapsed>.8:
            report['ammo_after']=prop(s.weapon,'Current Bullets');assert report['ammo_after']<report['ammo_before']
            s.player.character_movement.set_movement_mode(u.MovementMode.MOVE_FLYING)
            place((-5400,-4700,3200),(-24,40,0));s.fp_mesh.set_visibility(False,True)
            for a in s.weapon_visual.player_parts:a.set_actor_hidden_in_game(True)
            phase=6;elapsed=0
        elif phase==6 and elapsed>3 and shot('overview'):
            report['passed']=True;finish()
    except Exception:report['error']=traceback.format_exc();u.log_error(report['error']);finish()
handle=u.register_slate_post_tick_callback(tick)
