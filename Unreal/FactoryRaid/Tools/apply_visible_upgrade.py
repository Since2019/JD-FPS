"""Targeted weapon finish, full-map surfaces and ship panel construction."""
import unreal as u,os,json,shutil,traceback,runpy
T=os.path.dirname(__file__);ROOT=os.path.dirname(T);A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary;E=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
report={'passed':False,'materials':[],'maps':{}};D='/Game/Realism/Revision2'
def backup(path):
 rel=path.split('.')[0].replace('/Game/','')+('.umap' if '/Maps/' in path else '.uasset');src=os.path.join(ROOT,'Content',rel);dst=os.path.join(T,'VisibleUpgradeBackup',rel)
 if os.path.isfile(src) and not os.path.exists(dst):os.makedirs(os.path.dirname(dst),exist_ok=True);shutil.copy2(src,dst)
def node(m,c):return M.create_material_expression(m,c)
def val(m,v,p):
 e=node(m,u.MaterialExpressionConstant3Vector if isinstance(v,tuple) else u.MaterialExpressionConstant)
 if isinstance(v,tuple):e.constant=u.LinearColor(*v,1)
 else:e.r=v
 M.connect_material_property(e,'',p);return e
def custom(m,code,inputs,p,scalar=False):
 e=node(m,u.MaterialExpressionCustom);e.set_editor_property('code',code);e.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else u.CustomMaterialOutputType.CMOT_FLOAT3);args=[]
 for key in inputs:i=u.CustomInput();i.set_editor_property('input_name',key);args.append(i)
 e.set_editor_property('inputs',args)
 for key,n in inputs.items():M.connect_material_expressions(n,'',e,key)
 M.connect_material_property(e,'',p);return e
def material(path):
 backup(path);m=u.load_asset(path) or A.create_asset(path.rsplit('/',1)[1],path.rsplit('/',1)[0],u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m);return m
def save(m):M.recompile_material(m);assert u.EditorAssetLibrary.save_loaded_asset(m);report['materials'].append(m.get_path_name())
def texobj(m,t):e=node(m,u.MaterialExpressionTextureObject);e.texture=t;return e
try:
 # Rebuild actual weapon materials used by both regular launchers, retain authored UVs.
 for folder,mat,base,rough,normal,ao in [('HK416','Low','HK416BaseColorLow','HK416RoughnessLow2k','HK416NormalLowCompressed','HK416AOLow2k'),('HK416','Sights','HK416BaseColorSights','HK416RoughnessSights','HK416NormalSights','HK416AOSights'),('EOTechXPS3Scope','EOTechXPS3Mat','EotechXPS_Base_Color','EotechXPS_Roughness','EotechXPS_Normal_DirectX',None)]:
  prefix='/Game/Game/Assets/Models/Weapons/'+folder+'/';m=material(prefix+mat);uv=node(m,u.MaterialExpressionTextureCoordinate)
  base_t=u.load_asset(prefix+base);custom(m,'return clamp(Texture2DSample(Tex,TexSampler,UV).rgb*.18,float3(.008,.010,.012),float3(.085,.085,.085));',{'Tex':texobj(m,base_t),'UV':uv},u.MaterialProperty.MP_BASE_COLOR)
  custom(m,'return clamp(Texture2DSample(Tex,TexSampler,UV).r,.58,.9);',{'Tex':texobj(m,u.load_asset(prefix+rough)),'UV':uv},u.MaterialProperty.MP_ROUGHNESS,True)
  n=node(m,u.MaterialExpressionTextureSample);n.texture=u.load_asset(prefix+normal);n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
  custom(m,'return normalize(float3(N.xy*.35,N.z));',{'N':n},u.MaterialProperty.MP_NORMAL)
  if ao:
   n=node(m,u.MaterialExpressionTextureSample);n.texture=u.load_asset(prefix+ao);n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR);M.connect_material_property(n,'R',u.MaterialProperty.MP_AMBIENT_OCCLUSION)
  val(m,0.,u.MaterialProperty.MP_METALLIC);val(m,.22,u.MaterialProperty.MP_SPECULAR);save(m)
 # Import paired 4K surfaces with raw normal encoding for world-space projection.
 textures={}
 for item in json.load(open(os.path.join(T,'SurfaceUpgrade','manifest.json'))):
  textures[item['id']]={}
  for ch,f in item['files'].items():
   task=u.AssetImportTask();task.filename=f['path'];task.destination_path=D+'/Textures';task.destination_name=item['id']+'_'+ch;task.automated=True;task.save=True;task.replace_existing=True;A.import_asset_tasks([task]);tex=u.load_asset(task.imported_object_paths[0]);tex.set_editor_property('srgb',ch=='Diffuse');tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT);u.EditorAssetLibrary.save_loaded_asset(tex);textures[item['id']][ch]=tex
 def surface(path,source,scale,paint=False,factory=False):
  m=material(path);m.set_editor_property('tangent_space_normal',False);p=node(m,u.MaterialExpressionWorldPosition);n=node(m,u.MaterialExpressionVertexNormalWS)
  prefix='float3 w=pow(abs(N),8);w/=max(dot(w,1),.001);float3 q=P/'+str(float(scale))+';'
  for ch,prop in [('Diffuse',u.MaterialProperty.MP_BASE_COLOR),('Rough',u.MaterialProperty.MP_ROUGHNESS),('AO',u.MaterialProperty.MP_AMBIENT_OCCLUSION),('nor_dx',u.MaterialProperty.MP_NORMAL)]:
   inputs={'P':p,'N':n,'Tex':texobj(m,textures[source][ch])}
   code=prefix+'float3 a=Texture2DSample(Tex,TexSampler,q.yz).rgb;float3 b=Texture2DSample(Tex,TexSampler,q.xz).rgb;float3 c=Texture2DSample(Tex,TexSampler,q.xy).rgb;float3 v=a*w.x+b*w.y+c*w.z;'
   if ch=='Diffuse':
    code+=('float l=clamp(dot(v,float3(.2126,.7152,.0722))*2,.28,.85);return l*lerp(float3(.075,.18,.19),float3(.63,.62,.52),step(115,fmod(max(P.z,0),350)));' if paint else 'return v*lerp(float3(.30,.43,.32),float3(.85,.85,.83),step(125,max(P.z,0)));' if factory else 'return v*.8;')
   elif ch=='Rough':code+='return clamp(v.r,.65,.96);'
   elif ch=='AO':code+='return clamp(v.r,.5,1.);'
   else:code+='a=a*2-1;b=b*2-1;c=c*2-1;return normalize(float3(sign(N.x)*a.z,a.x*.18,a.y*.18)*w.x+float3(b.x*.18,sign(N.y)*b.z,b.y*.18)*w.y+float3(c.x*.18,c.y*.18,sign(N.z)*c.z)*w.z);'
   custom(m,code,inputs,prop,ch in ['Rough','AO'])
  val(m,0.,u.MaterialProperty.MP_METALLIC);val(m,.25,u.MaterialProperty.MP_SPECULAR);save(m);return m
 wall=surface(D+'/M_Bulkhead','blue_metal_plate',250,True)
 surface('/Game/Factory/Visual2/Materials/M_wall','concrete_wall_006',240,factory=True)
 surface('/Game/Factory/Visual2/Materials/M_floor','concrete_floor_02',200)
 # Existing diamond-plate normal was too strong and repeated at 50 cm.
 path='/Game/Icebreaker/Materials/M_Deck';backup(path);deck=u.load_asset(path)
 for e in u.ObjectIterator():
  if e.get_outer()==deck and isinstance(e,u.MaterialExpressionCustom):
   code=e.get_editor_property('code').replace('P/50.','P/150.').replace('*.5','*.18').replace('clamp(c.r,.4,.94)','clamp(c.r,.68,.94)');e.set_editor_property('code',code)
 save(deck)
 seam=material(D+'/M_PanelTrim');val(seam,(.045,.059,.058),u.MaterialProperty.MP_BASE_COLOR);val(seam,.72,u.MaterialProperty.MP_ROUGHNESS);val(seam,0.,u.MaterialProperty.MP_METALLIC);save(seam)
 cube=u.load_asset('/Engine/BasicShapes/Cube')
 for map_path in ['/Game/Icebreaker/Maps/Icebreaker','/Game/Factory/Maps/ClassicFactoryVisual']:
  backup(map_path);L.load_level(map_path);ice='Icebreaker' in map_path;changed=0;added=0
  actors=list(E.get_all_level_actors())
  for a in actors:
   if a.actor_has_tag('VisibleUpgradePanel'):E.destroy_actor(a)
  def strip(label,pos,size):
   a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos));a.set_actor_label(label);a.set_folder_path('Realism/BulkheadConstruction');a.tags=[u.Name('VisibleUpgradePanel')];c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,seam);c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False);a.set_actor_scale3d(u.Vector(*(x/100 for x in size)));return a
  for a in actors:
   if isinstance(a,u.StaticMeshActor) and ice and any(k in a.get_actor_label() for k in ['bulkhead','Bridge lower side','Bridge end bulkhead','Bridge upper side','Exhaust trunk']):
    for i in range(a.static_mesh_component.get_num_materials()):a.static_mesh_component.set_material(i,wall)
    changed+=1
   if isinstance(a,u.DirectionalLight) and ice:a.light_component.set_intensity(1800.);a.light_component.set_editor_property('light_source_angle',12.)
   if isinstance(a,u.PostProcessVolume) and ice:
    s=a.get_editor_property('settings');s.set_editor_property('auto_exposure_min_brightness',5.);s.set_editor_property('auto_exposure_bias',-.6);a.set_editor_property('settings',s)
  if ice:
   # Proposed insulated liner construction: 125 cm panel module, 2 cm seam cap.
   for y in [-530,530]:
    for x in range(-1475,1700,125):strip('Bulkhead vertical joint',(x,y,170),(2,2,330));added+=1
    for z in [12,115,330]:strip('Bulkhead horizontal trim',(100,y,z),(3190,2,3 if z!=12 else 20));added+=1
   for y in [-458,458]:
    for x in range(-100,1550,125):strip('Bridge liner joint',(x,y,418),(2,2,114));added+=1
    strip('Bridge lower kickplate',(700,y,372),(1690,2,20));added+=1
  report['maps'][map_path]={'wall_actors_changed':changed,'construction_parts':added};assert L.save_current_level()
 runpy.run_path(os.path.join(T,'balance_visible_lighting.py'))
 runpy.run_path(os.path.join(T,'reduce_weapon_glare.py'))
 report['passed']=True
except Exception:report['error']=traceback.format_exc();u.log_error(report['error'])
finally:open(os.path.join(T,'visible_upgrade_apply.json'),'w').write(json.dumps(report,indent=2))
