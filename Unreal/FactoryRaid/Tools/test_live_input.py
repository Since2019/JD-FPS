"""Manual/native input fixture: never injects inventory or weapon actions."""
import unreal as u,os,sys,time,json,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession
from loot_model import item,insert
u.EditorPythonScripting.set_keep_python_script_alive(True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker')
s=None;started=time.monotonic();requested=False;last=0.;events=[];killed=False
def finish():
    u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    global s,requested,last,killed
    try:
        if time.monotonic()-started>600 or os.path.exists(os.path.join(T,'live_input.stop')):finish();return
        if not requested:L.editor_request_begin_play();requested=True;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:
            pc=u.GameplayStatics.get_player_controller(world,0)
            if pc:u.GameplayStatics.get_game_mode(world).restart_player(pc)
            return
        if s is None:
            s=TacticalSession(world,p,True)
            insert(s.pack,item('FAST 风格头盔'));r=item('MK18 风格步枪');r['ammo']=7;insert(s.pack,r)
        s.update(dt)
        if s.clock>2 and not killed:
            # Death/GC regression with AI still enabled.
            for e in s.enemies:u.GameplayStatics.apply_damage(e['actor'],10000,s.pc,s.weapon,u.DamageType.static_class())
            killed=True;s.loot.open()
            equipment=s.loot.equipment;begin=equipment.begin;release=equipment.release
            def log_begin(*args,**kwargs):
                begin(*args,**kwargs);events.append({'event':'press','side':args[0],'pointer':[equipment.pointer().x,equipment.pointer().y]})
            def log_release(*args,**kwargs):
                events.append({'event':'release','pointer':[equipment.pointer().x,equipment.pointer().y],'drag':bool(equipment.drag)});release(*args,**kwargs)
            equipment.begin=log_begin;equipment.release=log_release
        if s.clock-last>.25:
            last=s.clock;e=s.loot.equipment
            data={'clock':s.clock,'inventory':s.inventory,'selected':e.selected,'slots':{k:(v['name'] if v else None) for k,v in e.slots.items()},'ammo':s.prop(s.weapon,'Current Bullets'),'pack':[i['name'] for i in s.pack],'events':events[-20:],'drag':bool(e.drag),'corpses':len(s.loot.corpses),'ai_enabled':s.ai_enabled}
            open(os.path.join(T,'live_input.json'),'w',encoding='utf-8').write(json.dumps(data,ensure_ascii=False,indent=2))
    except Exception:
        open(os.path.join(T,'live_input_error.txt'),'w',encoding='utf-8').write(traceback.format_exc());finish()
handle=u.register_slate_post_tick_callback(tick)
