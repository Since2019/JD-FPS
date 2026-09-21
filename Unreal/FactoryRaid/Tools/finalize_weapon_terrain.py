import unreal as u,os,json,runpy
T=os.path.dirname(__file__);D='/Game/Realism/WeaponTerrain';L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
L.load_level('/Game/Icebreaker/Maps/Icebreaker');report={}
for name in ['SM_ScannedSnowField','SM_ScannedSnowDrift']:
 sm=u.load_asset(D+'/'+name);b=sm.get_bounds();report[name]={'origin':[b.origin.x,b.origin.y,b.origin.z],'extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z]}
 if name=='SM_ScannedSnowField':
  for a in E.get_all_level_actors():
   if a.actor_has_tag('ScannedCoast') and 'snowfield' in a.get_actor_label():a.set_actor_location(u.Vector(-b.origin.x,3300-b.origin.y+b.box_extent.y,485),False,True)
assert L.save_current_level()
lib=u.get_default_object(u.load_class(None,'/Script/ProceduralMeshComponent.KismetProceduralMeshLibrary'))
report['rifle_triangles']={}
for suffix in ['', '_bolt_a','_bolt_b','_scope','_trigger','_wrap']:
 sm=u.load_asset(D+'/bolt_action_rifle_7_62/bolt_action_rifle_7_62'+suffix);count=0
 for section in range(len(sm.get_editor_property('static_materials'))):count+=len(lib.call_method('GetSectionFromStaticMesh',args=(sm,0,section))[1])//3
 report['rifle_triangles'][suffix or 'body']=count
open(os.path.join(T,'weapon_terrain_geometry_audit.json'),'w').write(json.dumps(report,indent=2))
runpy.run_path(os.path.join(T,'preview_bolt762.py'))
