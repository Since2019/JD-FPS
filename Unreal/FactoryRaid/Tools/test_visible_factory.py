import unreal as u,os,sys,time,json,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
ice=os.environ.get('RAID_REALISM_MAP')=='icebreaker';name='icebreaker' if ice else 'factory'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker' if ice else '/Game/Factory/Maps/ClassicFactoryVisual')
u.EditorPythonScripting.set_keep_python_script_alive(True);s=None;phase=0;elapsed=0.;start=time.monotonic();capture=None;report={'passed':False,'map':name,'rhi':'DX12 requested; verify log','frames':[]}
def finish():
    open(os.path.join(T,'visible_realism_'+name+'_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(label):
    global capture
    if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,os.path.join(T,'visible_realism_'+name+'_'+label+'.png'))
    if capture and capture.is_task_done():capture=None;return True
    return False
def tick(dt):
    global s,phase,elapsed
    try:
        if time.monotonic()-start>220:raise RuntimeError('Realism capture timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:s=TacticalSession(world,p,True);s.ai_enabled=False;s.pc.set_control_rotation(u.Rotator(yaw=0));elapsed=0
        s.update(dt,{'RightMouseButton'} if phase==2 else {'RightMouseButton','LeftMouseButton'} if phase==3 else set())
        if phase==1 and elapsed>5 and shot('hip'):
            report['enemies']=len(s.enemies);report['containers']=len(s.boxes)
            report['fp_materials']=[str(s.fp_mesh.get_material(i)) for i in range(s.fp_mesh.get_num_materials())]
            report['renderer_cvars']={key:u.SystemLibrary.get_console_variable_int_value(key) for key in ['r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.Shadow.Virtual.Enable']}
            assert len(s.enemies)==6 and len(s.boxes)>=1
            c=s.optic.holo.static_mesh_component;scale=c.get_editor_property('relative_scale3d');b=c.get_editor_property('static_mesh').get_bounds().box_extent
            report['holo_dimensions_cm']=[2*b.x*scale.x,2*b.y*scale.y,2*b.z*scale.z]
            assert all(abs(a-b)<.01 for a,b in zip(report['holo_dimensions_cm'],[9.65,5.33,6.35]))
            report['ammo_before']=prop(s.weapon,'Current Bullets');phase=2;elapsed=0
        elif phase==2 and elapsed>2 and shot('ads'):
            report['ads_error_cm']=s.aim_error;assert s.aim_error<.15;phase=3;elapsed=0
        elif phase==3 and elapsed>.5:
            assert prop(s.weapon,'Current Bullets')<report['ammo_before'];report['firing']=True
            if not ice:report['passed']=True;finish();return
            p.set_actor_location(u.Vector(-1380,0,98),False,True);s.pc.set_control_rotation(u.Rotator(yaw=0));phase=4;elapsed=0
        elif phase==4 and elapsed>5 and shot('engine'):
            assert 80<p.get_actor_location().z<120
            p.set_actor_location(u.Vector(500,0,458),False,True);s.pc.set_control_rotation(u.Rotator(yaw=0));phase=5;elapsed=0
        elif phase==5 and elapsed>5 and shot('bridge'):report['passed']=True;finish()
    except Exception:report['phase']=phase;report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)

