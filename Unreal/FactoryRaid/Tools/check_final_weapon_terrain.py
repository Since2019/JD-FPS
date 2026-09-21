import unreal as u,os,sys,time,json,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
from item_icons import texture
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker');u.EditorPythonScripting.set_keep_python_script_alive(True)
s=None;phase=0;elapsed=0;capture=None;start=time.monotonic();report={'passed':False}
def finish():
 open(os.path.join(T,'weapon_terrain_final_check.json'),'w').write(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(name):
 global capture
 if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1600,900,os.path.join(T,'final_assets_'+name+'.png'))
 if capture and capture.is_task_done():capture=None;return True
 return False
def advance():
 global phase,elapsed
 phase+=1;elapsed=0
def tick(dt):
 global s,phase,elapsed
 try:
  if time.monotonic()-start>220:raise RuntimeError('timeout')
  if phase==0:L.editor_request_begin_play();phase=1;return
  world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
  if not world:return
  p=u.GameplayStatics.get_player_character(world,0)
  if not p:return
  if s is None:
   s=TacticalSession(world,p,True);s.ai_enabled=False;p.set_actor_location(u.Vector(-3350,300,98),False,True);s.loot.equipment.select('primary2')
   report['icon']=texture(s.loot.equipment.loaded).get_path_name();assert report['icon'].endswith('Photo_Bolt762.Photo_Bolt762')
  s.pc.set_control_rotation(u.Rotator(yaw=90,pitch=-3 if phase<3 else -7))
  keys={'Tab'} if phase==2 and elapsed<.08 or phase==3 and elapsed<.08 else {'LeftMouseButton'} if phase==4 and (elapsed%1.4)<.15 else {'R'} if phase==5 and elapsed<.08 else {'One'} if phase==6 and elapsed<.08 else {'Two'} if phase==7 and elapsed<.08 else set()
  s.update(dt,keys);elapsed+=min(dt,.1)
  if phase==1 and elapsed>5 and shot('coast_rifle'):advance()
  elif phase==2 and elapsed>2 and shot('inventory'):
   assert s.inventory;advance()
  elif phase==3:
   if elapsed<.3:p.set_actor_location(u.Vector(500,0,458),False,True)
   if elapsed>5 and shot('snowfield'):advance()
  elif phase==4 and elapsed>8:
   report['ammo_after_empty']=prop(s.weapon,'Current Bullets');assert report['ammo_after_empty']==0;advance()
  elif phase==5 and elapsed>3.5:
   report['reloaded_from_empty']=prop(s.weapon,'Current Bullets');assert report['reloaded_from_empty']==5;advance()
  elif phase==6 and elapsed>1:
   assert s.weapon_visual.variant=='HK416';assert prop(s.weapon,'Current Bullets')==30;advance()
  elif phase==7 and elapsed>1:
   assert s.weapon_visual.variant=='BOLT';assert prop(s.weapon,'Current Bullets')==5;report['switch_roundtrip']=True;report['passed']=True;finish()
 except Exception:report['phase']=phase;report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)
