"""Rendered regression: moving ADS hands, world-mounted optic, lighting and PMC detail."""
import unreal as u,os,sys,json,time,traceback,math
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,length
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryVisual')
session=None;stage=0;elapsed=0.;began=time.monotonic();capture=None;frames=[];report={'passed':False}
def finish():
    open(os.path.join(T,'look_test.json'),'w',encoding='utf-8').write(json.dumps(report,indent=2,ensure_ascii=False))
    u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def screen(name):
    global capture
    if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,os.path.join(T,'look_'+name+'.png'))
    if capture and capture.is_task_done():capture=None;return True
    return False
def tick(dt):
    global session,stage,elapsed
    try:
        if time.monotonic()-began>160:raise RuntimeError('Look test timed out')
        elapsed+=min(dt,.1)
        if stage==0:L.editor_request_begin_play();stage=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if session is None:
            if elapsed<3:return
            session=TacticalSession(world,p,True);session.ai_enabled=False;session.pc.set_control_rotation(u.Rotator(yaw=0));elapsed=0
        if stage==3:
            p.add_movement_input(u.Vector(0,1,0),.55,True)
            session.pc.set_control_rotation(u.Rotator(yaw=12*math.sin(elapsed*1.5),pitch=2*math.sin(elapsed*2)))
        keys={'RightMouseButton'} if stage in [2,3,4] else set()
        session.update(dt,keys)
        if stage==1 and elapsed>3 and screen('hip'):
            report['crosshair_removed']=session.optic.crosshair_removed;report['ui']=session.optic.ui_report
            assert session.optic.crosshair_removed
            report['gear_count']=len(session.pmc.parts);assert report['gear_count']>=180
            stage=2;elapsed=0
        elif stage==2 and elapsed>2 and screen('ads'):
            log=open(os.path.join(T,'look_test.log'),encoding='utf-8',errors='replace').read()
            assert 'Failed to compile Material' not in log,'Material shader compilation failed'
            assert session.optic.parts[-1].static_mesh_component.get_material(0)==session.optic.lens
            report['ads_diagnostic']={'error':session.aim_error,'alignment':session.sight_alignment,'camera':str(session.camera.get_world_transform()),'arms':str(session.fp_mesh.get_world_transform())}
            assert session.pose_calibrated and session.fp_mesh.pause_anims
            assert session.aim_error<.2 and session.sight_alignment>.999
            report['start_pos']=[p.get_actor_location().x,p.get_actor_location().y,p.get_actor_location().z]
            stage=3;elapsed=0
        elif stage==3:
            hand=session.camera.get_world_transform().inverse_transform_location(session.fp_mesh.get_socket_location('hand_r'))
            frames.append({'hand':[hand.x,hand.y,hand.z],'error':session.aim_error,'alignment':session.sight_alignment})
            if elapsed>3:
                report['movement_cm']=length(p.get_actor_location()-u.Vector(*report['start_pos']))
                report['hand_jitter_cm']=max(length(u.Vector(*f['hand'])-u.Vector(*frames[0]['hand'])) for f in frames)
                report['max_sight_error_cm']=max(f['error'] for f in frames)
                assert report['movement_cm']>50
                assert report['hand_jitter_cm']<.12,report['hand_jitter_cm']
                assert report['max_sight_error_cm']<.2
                session.pc.set_control_rotation(u.Rotator(yaw=0));stage=4;elapsed=0
        elif stage==4 and elapsed>1 and screen('moving_ads'):
            p.set_actor_location(u.Vector(-2850,2500,98),False,True);session.pc.set_control_rotation(u.Rotator(yaw=0,pitch=-5))
            npc=session.enemies[0]['actor'];npc.set_actor_location(u.Vector(-2520,2500,98),False,True);npc.set_actor_rotation(u.Rotator(yaw=180),False)
            stage=5;elapsed=0
        elif stage==5 and elapsed>3 and screen('pmc'):
            p.set_actor_location(u.Vector(-1800,-3000,-242),False,True);session.pc.set_control_rotation(u.Rotator(yaw=0,pitch=0));stage=6;elapsed=0
        elif stage==6 and elapsed>3 and screen('tunnel'):
            report['passed']=True;report['frames']=frames;finish()
    except Exception:report['error']=traceback.format_exc();report['stage']=stage;finish()
handle=u.register_slate_post_tick_callback(tick)
