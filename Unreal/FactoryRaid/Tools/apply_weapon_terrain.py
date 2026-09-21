import unreal as u,os,json,traceback,shutil
T=os.path.dirname(__file__);A=u.AssetToolsHelpers.get_asset_tools();E=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);M=u.MaterialEditingLibrary
D='/Game/Realism/WeaponTerrain';R={'passed':False}
try:
 mesh=u.load_asset(D+'/bolt_action_rifle_7_62/bolt_action_rifle_7_62_scope')
 lib=u.get_default_object(u.load_class(None,'/Script/ProceduralMeshComponent.KismetProceduralMeshLibrary'))
 data=lib.call_method('GetSectionFromStaticMesh',args=(mesh,0,1));vs=list(data[0])
 lo=[min(getattr(v,k) for v in vs) for k in ['x','y','z']];hi=[max(getattr(v,k) for v in vs) for k in ['x','y','z']]
 R['glass_bounds']=[lo,hi];R['mount']=[(lo[1]+hi[1])/2,-lo[0],18.5-(lo[2]+hi[2])/2];R['lens_radius']=max(hi[1]-lo[1],hi[2]-lo[2])/2
 m=A.create_asset('M_BoltLens',D,u.Material,u.MaterialFactoryNew()) if not u.load_asset(D+'/M_BoltLens') else u.load_asset(D+'/M_BoltLens')
 M.delete_all_material_expressions(m);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);m.set_editor_property('two_sided',True)
 c=M.create_material_expression(m,u.MaterialExpressionCustom);c.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
 c.set_editor_property('code','float2 q=float2(dot(P-Center,Right),-dot(P-Center,Up))/(2*Radius); float2 uv=q+.5; float cross=max((1-smoothstep(.002,.004,abs(q.x))),(1-smoothstep(.002,.004,abs(q.y)))); float3 scene=Texture2DSample(ScopeView,ScopeViewSampler,uv).rgb; return lerp(float3(.013,.020,.021),scene*(1-cross)*smoothstep(.50,.39,length(q)),Active);')
 nodes={}
 nodes['P']=M.create_material_expression(m,u.MaterialExpressionWorldPosition)
 for name in ['Center','Right','Up']:
  n=M.create_material_expression(m,u.MaterialExpressionVectorParameter);n.set_editor_property('parameter_name',name);nodes[name]=n
 for name,value in [('Radius',R['lens_radius']),('Active',0.)]:
  n=M.create_material_expression(m,u.MaterialExpressionScalarParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);nodes[name]=n
 n=M.create_material_expression(m,u.MaterialExpressionTextureObjectParameter);n.set_editor_property('parameter_name','ScopeView');n.texture=u.load_asset('/Engine/EngineResources/WhiteSquareTexture');nodes['ScopeView']=n
 inputs=[]
 for name in nodes:
  i=u.CustomInput();i.set_editor_property('input_name',name);inputs.append(i)
 c.set_editor_property('inputs',inputs)
 for name,n in nodes.items():M.connect_material_expressions(n,'',c,name)
 M.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
 terrain={}
 for name,mat in [('SM_ScannedSnowField','snow_field_aerial'),('SM_ScannedSnowDrift','snow_02')]:
  task=u.AssetImportTask();task.filename=os.path.join(T,'WeaponTerrainSource',name+'.obj');task.destination_path=D;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
  opt=u.FbxImportUI();opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.set_editor_property('automated_import_should_detect_type',False);opt.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False;task.options=opt
  A.import_asset_tasks([task]);sm=next(u.load_asset(p) for p in task.imported_object_paths if isinstance(u.load_asset(p),u.StaticMesh));sm.set_material(0,u.load_asset(D+'/'+mat+'/M_Main'));u.EditorAssetLibrary.save_loaded_asset(sm);terrain[name]=sm
 src=os.path.join(os.path.dirname(T),'Content','Icebreaker','Maps','Icebreaker.umap');dst=os.path.join(T,'WeaponTerrainBackup','Icebreaker.umap')
 if not os.path.exists(dst):shutil.copy2(src,dst)
 L.load_level('/Game/Icebreaker/Maps/Icebreaker')
 for a in list(E.get_all_level_actors()):
  if a.actor_has_tag('ScannedCoast'):E.destroy_actor(a)
 def spawn(name,mesh,pos,yaw=0):
  a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(yaw=yaw));a.set_actor_label(name);a.tags=[u.Name('ScannedCoast')];a.set_folder_path('Realism/ScannedCoast');a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False);return a
 cliff=u.load_asset(D+'/coastal_cliff_02/coastal_cliff_02_LOD0')
 for x in [-1980,1980]:spawn('PH | 41m scanned coastal cliff',cliff,(x,2950,-480),180)
 spawn('PH | 80m snowfield',terrain['SM_ScannedSnowField'],(0,3200,485))
 count=0
 for a in E.get_all_level_actors():
  if isinstance(a,u.StaticMeshActor) and 'Deck snow drift' in a.get_actor_label():
   pos=a.get_actor_location();a.static_mesh_component.set_static_mesh(terrain['SM_ScannedSnowDrift']);a.set_actor_scale3d(u.Vector(1,1,1));a.set_actor_location(u.Vector(pos.x,pos.y,1),False,True);a.static_mesh_component.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False);count+=1
 R['drifts_replaced']=count;R['coast_pieces']=3;assert L.save_current_level();R['passed']=True
except Exception:R['error']=traceback.format_exc();u.log_error(R['error'])
finally:open(os.path.join(T,'weapon_terrain_apply.json'),'w').write(json.dumps(R,indent=2))

