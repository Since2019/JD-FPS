import unreal as u,os,sys,time,json,traceback
T=os.path.dirname(__file__);sys.path.insert(0,T)
from tactical_runtime import TacticalSession,prop
factory=os.environ.get('RAID_TEST_FACTORY')=='1';label='factory' if factory else 'icebreaker'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryVisual' if factory else '/Game/Icebreaker/Maps/Icebreaker');u.EditorPythonScripting.set_keep_python_script_alive(True)
s=None;phase=0;elapsed=0;capture=None;start=time.monotonic();report={'passed':False}
def finish():
 open(os.path.join(T,'weapon_terrain_'+label+'_test.json'),'w').write(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def shot(name):
 global capture
 if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1600,900,os.path.join(T,'new_assets_'+label+'_'+name+'.png'))
 if capture and capture.is_task_done():capture=None;return True
 return False
def advance():
 global phase,elapsed
 phase+=1;elapsed=0
def tick(dt):
 global s,phase,elapsed
 try:
  if time.monotonic()-start>280:raise RuntimeError('timeout')
  if phase==0:L.editor_request_begin_play();phase=1;return
  world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
  if not world:return
  p=u.GameplayStatics.get_player_character(world,0)
  if not p:return
  if s is None:
   s=TacticalSession(world,p,True);s.ai_enabled=False;s.pc.set_control_rotation(u.Rotator(yaw=0 if factory else 90));report['enemies']=len(s.enemies);report['containers']=len(s.boxes);report['terrain_actors']=len([a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if a.actor_has_tag('ScannedCoast') or a.actor_has_tag('CoastExtension')]);assert report['terrain_actors']==(0 if factory else 7)
   if not factory:p.set_actor_location(u.Vector(-3350,300,98),False,True)
  if not factory:s.pc.set_control_rotation(u.Rotator(yaw=90,pitch=-3))
  keys={'Two'} if phase==2 and elapsed<.15 else {'RightMouseButton'} if phase==3 else {'LeftMouseButton'} if phase==4 else {'R'} if phase==6 and elapsed<.15 else {'One'} if phase==7 and elapsed<.15 else set()
  s.update(dt,keys);elapsed+=min(dt,.1)
  if phase==1 and elapsed>6 and shot('coast_hk'):advance()
  elif phase==2 and elapsed>4 and shot('rifle_hip'):
   assert s.weapon_visual.variant=='BOLT';report['rifle_parts']=len(s.weapon_visual.bolt.parts);assert report['rifle_parts']==6;report['ammo_initial']=prop(s.weapon,'Current Bullets');assert report['ammo_initial']==5
   for a in s.weapon_visual.bolt.parts:assert str(a.static_mesh_component.get_collision_profile_name())=='NoCollision'
   advance()
  elif phase==3 and elapsed>3 and shot('rifle_ads'):report['ads_error_cm']=s.aim_error;assert s.aim_error<.15;advance()
  elif phase==4 and elapsed>2:
   report['ammo_after_hold']=prop(s.weapon,'Current Bullets');assert report['ammo_after_hold']==4;advance()
  elif phase==5 and elapsed>.3:advance()
  elif phase==6 and elapsed>3.5:
   report['ammo_after_reload']=prop(s.weapon,'Current Bullets');assert report['ammo_after_reload']==5;advance()
  elif phase==7 and elapsed>1:
   assert s.weapon_visual.variant=='HK416';assert prop(s.weapon,'Current Bullets')==30;report['switch_ammo_preserved']=True;report['passed']=True;finish()
 except Exception:report['phase']=phase;report['error']=traceback.format_exc();finish()
handle=u.register_slate_post_tick_callback(tick)
