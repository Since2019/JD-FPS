import unreal as u,os,sys,time,json,traceback,glob,shutil
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker')
s=None;phase=0;elapsed=0.;started=time.monotonic();capture=None;report={'passed':False}
def finish():
    open(os.path.join(T,'loot_ui_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(name):
    global capture
    path=os.path.join(T,'loot_ui_'+name+'.png')
    if capture is None:
        capture=time.time();u.SystemLibrary.execute_console_command(s.world,'Shot showui filename="'+path.replace('\\','/')+'"');return False
    matches=[p for p in glob.glob(path[:-4]+'*.png') if os.path.getmtime(p)>=capture]
    if matches:
        source=max(matches,key=os.path.getmtime)
        if source!=path:shutil.copyfile(source,path)
        capture=None;return True
    if time.time()-capture>3:raise RuntimeError('UI screenshot missing: '+path)
    return False
def tick(dt):
    global s,phase,elapsed
    try:
        if time.monotonic()-started>160:raise RuntimeError('Loot test timeout')
        elapsed+=min(dt,.1)
        if phase==0:L.editor_request_begin_play();phase=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if s is None:
            if elapsed<3:return
            s=TacticalSession(world,p,True);s.ai_enabled=False;p.set_actor_location(u.Vector(-3640,-210,98),False,True);s.pc.set_control_rotation(u.Rotator(pitch=-34,yaw=0));elapsed=0
            report['arm_materials']=[m.get_path_name() for m in s.fp_mesh.get_materials() if m]
        s.update(dt,set())
        if phase==1 and elapsed>2:
            assert s.focus;s.update(.01,{'F'});assert s.inventory;phase=2;elapsed=0
        elif phase==2 and elapsed>.3 and shot('unknown'):
            assert s.pc.show_mouse_cursor;report['opened_by_f']=True;phase=3;elapsed=0
        elif phase==3 and elapsed>4 and shot('container'):
            target=s.loot.active;report['revealed']=sum(i['known'] for i in target['items']);assert report['revealed']==4
            original=target['items'][0];s.loot.click_item('Loot',0);assert original in s.pack and original not in target['items']
            s.loot.close();s.loot.open(target);assert original not in target['items'];report['transfer_persists']=True
            s.loot.close();s.update(.01,{'Escape'});assert not s.inventory
            e=s.enemies[0];e['actor'].set_actor_location(u.Vector(-3350,-210,98),False,True)
            u.GameplayStatics.apply_damage(e['actor'],10000,s.pc,s.weapon,u.DamageType.static_class())
            phase=4;elapsed=0
        elif phase==4 and elapsed>3:
            assert len(s.loot.corpses)==1,'Killed PMC must have persistent corpse';corpse=s.loot.corpses[0]
            pos=corpse['actor'].skeletal_mesh_component.get_socket_location('pelvis');p.set_actor_location(pos+u.Vector(-120,0,95),False,True);s.pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(p.get_actor_location()+u.Vector(0,0,64),pos))
            phase=41;elapsed=0
        elif phase==41 and elapsed>.6:
            assert s.focus and s.focus.get('corpse'),'Corpse must be targetable through the world interaction trace'
            s.update(.01,{'F'});assert s.inventory and s.loot.active['corpse'];report['corpse_opened_by_f']=True;phase=5;elapsed=0
        elif phase==5 and elapsed>6 and shot('corpse'):
            assert s.loot.active and s.loot.active['corpse'];names=[i['name'] for i in s.loot.active['items']];assert 'FAST 风格头盔' in names and 'MK18 风格步枪' in names
            s.loot.take_all();report['corpse_looted']=any(i['name']=='FAST 风格头盔' for i in s.pack);assert report['corpse_looted']
            s.loot.close();assert not s.pc.show_mouse_cursor;phase=6;elapsed=0
        elif phase==6 and elapsed>1 and shot('body'):
            report['passed']=True;finish()
    except Exception:report['error']=traceback.format_exc();u.log_error(report['error']);finish()
handle=u.register_slate_post_tick_callback(tick)
