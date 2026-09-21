import unreal as u,os,sys,json,time,traceback,math
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop,length
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryVisual')
s=None;phase=0;elapsed=0.;began=time.monotonic();capture=None;report={'passed':False};run_frames=[];late=None
def finish():
    open(os.path.join(T,'mk18_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
    u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(name):
    global capture
    if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,os.path.join(T,'mk18_'+name+'.png'))
    if capture and capture.is_task_done():capture=None;return True
    return False
def tick(dt):
    global s,phase,elapsed,late
    try:
        if time.monotonic()-began>180:raise RuntimeError('MK18 test timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:
            if elapsed<3:return
            s=TacticalSession(world,p,True);s.ai_enabled=False;s.pc.set_control_rotation(u.Rotator(yaw=0));elapsed=0
        keys=set()
        if phase in [2,4]:keys={'RightMouseButton'}
        if phase==3:
            keys={'LeftShift','W','RightMouseButton','LeftMouseButton'};p.add_movement_input(u.Vector(0,1,0),.8,True)
        if phase==5:keys={'LeftMouseButton','RightMouseButton'}
        s.update(dt,keys)
        if phase==1 and elapsed>3 and shot('hip'):
            report['weapons_replaced']=len(s.weapon_visual.applied);assert report['weapons_replaced']==7
            gun=next(c for c in s.weapon.get_components_by_class(u.SkeletalMeshComponent) if c.get_name()=='FP_Weapon')
            report['muzzle_local']=str(gun.get_socket_transform('Muzzle',u.RelativeTransformSpace.RTS_COMPONENT))
            report['original_mesh_material']=str(gun.get_material(0));assert 'M_HiddenTemplate' in report['original_mesh_material']
            phase=2;elapsed=0
        elif phase==2 and elapsed>1.5 and shot('ads'):
            assert s.aim_error<.15;report['ads_error_cm']=s.aim_error
            report['ammo_before_run']=prop(s.weapon,'Current Bullets');phase=3;elapsed=0
        elif phase==3:
            if elapsed>1:
                hand=s.camera.get_world_transform().inverse_transform_location(s.fp_mesh.get_socket_location('hand_r'));run_frames.append([hand.x,hand.y,hand.z])
            if elapsed>2. and shot('sprint'):
                assert s.sprinting and s.sprint_alpha>.98 and s.ads<.01
                assert prop(s.weapon,'Current Bullets')==report['ammo_before_run'],'Trigger fired during sprint'
                report['run_pose']={'alpha':s.sprint_alpha,'ads':s.ads,'hand':run_frames[-1]}
                report['run_bob_range_cm']=max(length(u.Vector(*f)-u.Vector(*run_frames[0])) for f in run_frames)
                assert .20<report['run_bob_range_cm']<3
                p.character_movement.stop_movement_immediately();phase=4;elapsed=0
        elif phase==4 and elapsed>1.6:
            assert s.sprint_alpha<.01 and s.ads>.99 and s.aim_error<.15
            report['recovered_ads']=True;report['ammo_before_fire']=prop(s.weapon,'Current Bullets');phase=5;elapsed=0
        elif phase==5 and elapsed>1.2:
            report['ammo_after_fire']=prop(s.weapon,'Current Bullets');assert report['ammo_after_fire']<report['ammo_before_fire']
            late=s.optic.widget_library.call_method('Create',args=(world,s.optic.widget_class,s.pc));late.call_method('AddToViewport',args=(0,))
            assert late.call_method('IsInViewport');phase=6;elapsed=0
        elif phase==6 and elapsed>.5:
            assert not late.call_method('IsInViewport'),'Late-created crosshair HUD survived'
            assert not s.pc.show_mouse_cursor;report['late_hud_removed']=True
            p.set_actor_location(u.Vector(-2800,2500,98),False,True);s.pc.set_control_rotation(u.Rotator(yaw=0,pitch=-8))
            npc=s.enemies[0]['actor'];npc.set_actor_location(u.Vector(-2590,2500,98),False,True);npc.set_actor_rotation(u.Rotator(yaw=165),False)
            s.fp_mesh.set_visibility(False,False)
            for a in s.weapon_visual.player_parts+s.optic.parts:a.set_actor_hidden_in_game(True)
            phase=7;elapsed=0
        elif phase==7 and elapsed>2 and shot('pmc'):
            log=open(os.path.join(T,'mk18_test.log'),encoding='utf-8',errors='replace').read();assert 'Failed to compile Material' not in log
            report['passed']=True;finish()
    except Exception:report['phase']=phase;report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)
