import unreal as u,os,sys,json,time,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryVisual')
s=None;phase=0;elapsed=0.;began=time.monotonic();capture=None;report={'passed':False}
def finish():
    open(os.path.join(T,'hk416_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
    u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(name):
    global capture
    if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,os.path.join(T,'hk416_'+name+'.png'))
    if capture and capture.is_task_done():capture=None;return True
    return False
def tick(dt):
    global s,phase,elapsed
    try:
        if time.monotonic()-began>180:raise RuntimeError('HK416 test timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:s=TacticalSession(world,p,True);s.ai_enabled=False;s.pc.set_control_rotation(u.Rotator(yaw=0));elapsed=0
        s.update(dt,{'RightMouseButton'} if phase in (2,4) else {'RightMouseButton','LeftMouseButton'} if phase==3 else set())
        e=s.loot.equipment
        if phase==1 and elapsed>4 and shot('hip'):
            assert e.loaded['name']=='HK416';assert s.weapon_visual.variant==s.optic.variant=='HK416';phase=2;elapsed=0
        elif phase==2 and elapsed>2 and shot('ads'):
            report['ads_error_cm']=s.aim_error;assert s.aim_error<.15;report['before']=prop(s.weapon,'Current Bullets');phase=3;elapsed=0
        elif phase==3 and elapsed>.7:
            report['after']=prop(s.weapon,'Current Bullets');assert report['after']<report['before'];e.select('primary2');phase=4;elapsed=0
        elif phase==4 and elapsed>2 and shot('mk18_ads'):
            assert s.optic.variant=='MK18';assert prop(s.weapon,'Current Bullets')==30;e.select('primary1');phase=5;elapsed=0
        elif phase==5 and elapsed>1:
            assert prop(s.weapon,'Current Bullets')==report['after'];report['switch_ammo_preserved']=True;report['passed']=True;finish()
    except Exception:report['phase']=phase;report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)
