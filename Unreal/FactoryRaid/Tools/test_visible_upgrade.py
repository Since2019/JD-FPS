import unreal as u,os,sys,json,time,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker');u.EditorPythonScripting.set_keep_python_script_alive(True)
s=None;phase=0;elapsed=0;capture=None;start=time.monotonic();report={'passed':False};views=[('service',(-1500,50,98),48,-22),('crate',(-1460,-100,98),-62,-28),('deck',(-3550,-520,98),0,0),('bridge',(500,0,458),0,0)]
def finish():
    open(os.path.join(T,'visible_test.json'),'w').write(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    global s,phase,elapsed,capture
    try:
        if time.monotonic()-start>200:raise RuntimeError('timeout')
        if phase==0:L.editor_request_begin_play();phase=1;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:
            s=TacticalSession(world,p,True);s.ai_enabled=False;s.pc.set_ignore_look_input(True)
            report['enemies']=len(s.enemies);report['containers']=len(s.boxes);assert len(s.enemies)==6 and len(s.boxes)==6
        s.update(dt,set());elapsed+=min(dt,.1)
        idx=phase-1
        if idx<len(views):
            name,pos,yaw,pitch=views[idx]
            if elapsed<.3:
                p.set_actor_location(u.Vector(*pos),False,True);s.pc.set_control_rotation(u.Rotator(yaw=yaw,pitch=pitch))
                for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor):
                    if str(a.get_actor_label()).startswith('PH Service |'):a.set_actor_hidden_in_game(name=='before')
            if elapsed>6:
                if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1600,900,os.path.join(T,'visible_'+name+'.png'))
                elif capture.is_task_done():capture=None;phase+=1;elapsed=0
        else:
            report['assets']=len([a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if str(a.get_actor_label()).startswith('PH Service |')]);assert report['assets']==3
            report['passed']=True;finish()
    except Exception:report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)


