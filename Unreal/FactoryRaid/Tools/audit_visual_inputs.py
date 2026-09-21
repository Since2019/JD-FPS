import unreal as u,os,json
T=os.path.dirname(__file__);out={}
for path in ['/Game/Game/Assets/Models/Weapons/HK416/Low','/Game/Game/Assets/Models/Weapons/EOTechXPS3Scope/EOTechXPS3Mat']:
 m=u.load_asset(path);nodes=[]
 for e in u.ObjectIterator():
  if e.get_outer()!=m:continue
  d={'class':e.get_class().get_name(),'name':e.get_name()}
  if isinstance(e,(u.MaterialExpressionTextureSample,u.MaterialExpressionTextureObject)):
   t=e.get_editor_property('texture');d['texture']=t.get_path_name() if t else None
  if isinstance(e,u.MaterialExpressionCustom):d['code']=e.get_editor_property('code')
  if isinstance(e,u.MaterialExpressionConstant):d['r']=e.r
  nodes.append(d)
 out[path]=nodes
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
for path in ['/Game/Icebreaker/Maps/Icebreaker','/Game/Factory/Maps/ClassicFactoryVisual']:
 L.load_level(path);out[path]=[]
 for a in E.get_all_level_actors():
  if isinstance(a,u.StaticMeshActor):
   o,b=a.get_actor_bounds(False)
   if max(b.x,b.y,b.z)>250:out[path].append({'label':a.get_actor_label(),'pos':[o.x,o.y,o.z],'size':[b.x*2,b.y*2,b.z*2],'materials':[a.static_mesh_component.get_material(i).get_path_name() for i in range(a.static_mesh_component.get_num_materials()) if a.static_mesh_component.get_material(i)]})
  elif isinstance(a,u.DirectionalLight):out[path].append({'sun':a.light_component.intensity})
open(os.path.join(T,'visual_input_audit.json'),'w').write(json.dumps(out,indent=2))
