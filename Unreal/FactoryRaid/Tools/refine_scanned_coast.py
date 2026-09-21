import unreal as u,os,json,traceback,runpy
T=os.path.dirname(__file__);D='/Game/Realism/WeaponTerrain';M=u.MaterialEditingLibrary;A=u.AssetToolsHelpers.get_asset_tools();L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem);R={'passed':False}
try:
 m=u.load_asset(D+'/M_SnowRock') or A.create_asset('M_SnowRock',D,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
 def node(cls):return M.create_material_expression(m,cls)
 def custom(code,inputs,scalar=False):
  c=node(u.MaterialExpressionCustom);c.set_editor_property('code',code);c.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else u.CustomMaterialOutputType.CMOT_FLOAT3);args=[]
  for name in inputs:i=u.CustomInput();i.set_editor_property('input_name',name);args.append(i)
  c.set_editor_property('inputs',args)
  for name,n in inputs.items():M.connect_material_expressions(n,'',c,name)
  return c
 p=node(u.MaterialExpressionWorldPosition);n=node(u.MaterialExpressionVertexNormalWS)
 mask=custom('return smoothstep(.45,.82,N.z)*smoothstep(160,440,P.z);',{'P':p,'N':n},True)
 uv=node(u.MaterialExpressionCustom);uv.set_editor_property('code','return P.xy/200.;');uv.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT2);i=u.CustomInput();i.set_editor_property('input_name','P');uv.set_editor_property('inputs',[i]);M.connect_material_expressions(p,'',uv,'P')
 for ch,prop in [('Diffuse',u.MaterialProperty.MP_BASE_COLOR),('Rough',u.MaterialProperty.MP_ROUGHNESS),('AO',u.MaterialProperty.MP_AMBIENT_OCCLUSION),('nor_dx',u.MaterialProperty.MP_NORMAL)]:
  a=node(u.MaterialExpressionTextureSample);a.texture=u.load_asset(D+'/coastal_cliff_02/T_'+ch);a.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR if ch=='Diffuse' else u.MaterialSamplerType.SAMPLERTYPE_NORMAL if ch=='nor_dx' else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
  if ch=='nor_dx':blend=custom('return normalize(lerp(A,float3(0,0,1),Mask*.9));',{'A':a,'Mask':mask})
  else:
   b=node(u.MaterialExpressionTextureSample);b.texture=u.load_asset(D+'/snow_02/T_'+ch);b.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR if ch=='Diffuse' else u.MaterialSamplerType.SAMPLERTYPE_MASKS);M.connect_material_expressions(uv,'',b,'UVs');blend=custom('return lerp(A,B,Mask);',{'A':a,'B':b,'Mask':mask})
  M.connect_material_property(blend,'',prop)
 M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
 L.load_level('/Game/Icebreaker/Maps/Icebreaker');cliff=u.load_asset(D+'/coastal_cliff_02/coastal_cliff_02_LOD0')
 for a in list(E.get_all_level_actors()):
  if a.actor_has_tag('CoastExtension'):E.destroy_actor(a)
  elif a.actor_has_tag('ScannedCoast') and 'cliff' in a.get_actor_label():a.static_mesh_component.set_material(0,m)
  elif isinstance(a,u.StaticMeshActor) and 'Deck snow drift' in a.get_actor_label():a.static_mesh_component.set_material(0,u.load_asset(D+'/snow_02/M_Main'))
 for x,y,yaw in [(-5870,3180,173),(5870,3180,187),(-9660,4130,158),(9660,4130,202)]:
  a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,-480),u.Rotator(yaw=yaw));a.set_actor_label('PH | Scanned coast extension');a.tags=[u.Name('CoastExtension')];a.set_folder_path('Realism/ScannedCoast');a.static_mesh_component.set_static_mesh(cliff);a.static_mesh_component.set_material(0,m);a.static_mesh_component.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
 assert L.save_current_level();R['passed']=True
except Exception:R['error']=traceback.format_exc();u.log_error(R['error'])
finally:open(os.path.join(T,'coast_refine.json'),'w').write(json.dumps(R,indent=2))
if R['passed']:runpy.run_path(os.path.join(T,'preview_bolt762.py'))
