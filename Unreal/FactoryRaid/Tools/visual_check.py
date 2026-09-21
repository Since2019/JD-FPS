import unreal as u, os, sys, time, traceback, json
TOOLS=os.path.dirname(__file__);sys.path.insert(0,TOOLS)
from tactical_runtime import TacticalSession,prop
u.EditorPythonScripting.set_keep_python_script_alive(True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level('/Game/Factory/Maps/ClassicFactoryTactical')
elapsed=0;requested=False;session=None;stage=0;report=[];capture=None
stages=[('hip',set()),('ads',{'RightMouseButton'}),('left',{'Q'}),('right',{'E'}),('lean_ads',{'Q','RightMouseButton'}),('fire',{'RightMouseButton'})]
def tick(dt):
    global elapsed,requested,session,stage,capture
    try:
        if not requested:level.editor_request_begin_play();requested=True;return
        elapsed+=min(dt,.1)
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if session is None:
            if elapsed<3:return
            session=TacticalSession(world,p,True);session.ai_enabled=False
            session.pc.set_control_rotation(u.Rotator(pitch=0,yaw=0,roll=0));elapsed=0
        name,keys=stages[stage]
        session.update(dt,keys)
        if name=='fire' and elapsed>1:session.weapon.call_method('Start Firing')
        if elapsed>3 and capture is None:
            path=os.path.join(TOOLS,'view_'+name+'.png')
            capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,path)
            report.append({'stage':name,'camera':str(session.camera.get_world_transform()),'aim_error':session.aim_error,'alignment':session.sight_alignment,'fp':str(session.fp_mesh.get_world_transform())})
        if capture is not None and capture.is_task_done():
            capture=None;stage+=1;elapsed=0
            if stage==len(stages):
                open(os.path.join(TOOLS,'visual_check.json'),'w').write(json.dumps(report,indent=2))
                u.unregister_slate_post_tick_callback(handle)
                # Keep this rendered preview open for observation.
                global finish_handle
                finish_time=time.monotonic()
                def finish(dt):
                    if time.monotonic()-finish_time<2:return
                    u.unregister_slate_post_tick_callback(finish_handle);level.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
                finish_handle=u.register_slate_post_tick_callback(finish)
    except:
        open(os.path.join(TOOLS,'visual_error.txt'),'w').write(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
handle=u.register_slate_post_tick_callback(tick)
