import unreal as u,os,json,traceback
T=os.path.dirname(__file__);A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary;out={'passed':False,'assets':{}}
def imp(path,dest,name,mesh=False):
 task=u.AssetImportTask();task.filename=path;task.destination_path=dest;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
 if mesh:
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False;opt.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opt.set_editor_property('automated_import_should_detect_type',False);opt.static_mesh_import_data.combine_meshes=False;opt.static_mesh_import_data.auto_generate_collision=False;opt.static_mesh_import_data.import_mesh_lo_ds=True;task.options=opt
 A.import_asset_tasks([task]);return [u.load_asset(p) for p in task.imported_object_paths]
def mat(dest,name,tex,prefix=''):
 m=u.load_asset(dest+'/'+name) or A.create_asset(name,dest,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
 channels={'Diffuse':u.MaterialProperty.MP_BASE_COLOR,'nor_dx':u.MaterialProperty.MP_NORMAL,'Rough':u.MaterialProperty.MP_ROUGHNESS,'Metal':u.MaterialProperty.MP_METALLIC,'AO':u.MaterialProperty.MP_AMBIENT_OCCLUSION}
 for ch,p in channels.items():
  key=ch if not prefix else prefix+{'Diffuse':'diff','nor_dx':'nor_dx','Rough':'rough','Metal':'metal','AO':'ao'}[ch]
  if key not in tex:continue
  n=M.create_material_expression(m,u.MaterialExpressionTextureSample);n.texture=tex[key];n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL if ch=='nor_dx' else u.MaterialSamplerType.SAMPLERTYPE_COLOR if ch=='Diffuse' else u.MaterialSamplerType.SAMPLERTYPE_MASKS);M.connect_material_property(n,'RGB' if ch in ['Diffuse','nor_dx'] else 'R',p)
 if prefix+'alpha' in tex:
  m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('two_sided',True);n=M.create_material_expression(m,u.MaterialExpressionTextureSample);n.texture=tex[prefix+'alpha'];n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_MASKS);M.connect_material_property(n,'R',u.MaterialProperty.MP_OPACITY_MASK)
 M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);return m
try:
 for item in json.load(open(os.path.join(T,'WeaponTerrainSource','manifest.json'))):
  name=item['id'];dest='/Game/Realism/WeaponTerrain/'+name;tex={}
  for ch,f in item['files'].items():
   if ch in ['mesh','Displacement']:continue
   t=next(x for x in imp(f['path'],dest,'T_'+ch) if isinstance(x,u.Texture2D));t.set_editor_property('srgb',ch in ['Diffuse','accesories_diff']);t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if 'nor_dx' in ch else u.TextureCompressionSettings.TC_DEFAULT if ch in ['Diffuse','accesories_diff'] else u.TextureCompressionSettings.TC_MASKS);u.EditorAssetLibrary.save_loaded_asset(t);tex[ch]=t
  main=mat(dest,'M_Main',tex);acc=mat(dest,'M_Accessories',tex,'accesories_') if 'accesories_diff' in tex else main
  data={'textures':{k:v.get_path_name() for k,v in tex.items()},'meshes':[],'source_info':item['info']}
  if 'mesh' in item['files']:
   meshes=[x for x in imp(item['files']['mesh']['path'],dest,'SM_'+name,True) if isinstance(x,u.StaticMesh)]
   for mesh in meshes:
    slots=[]
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
     sn=str(slot.get_editor_property('material_slot_name'));slots.append(sn);mesh.set_material(i,acc if 'acces' in sn.lower() else main)
    b=mesh.get_bounds();d={'path':mesh.get_path_name(),'name':mesh.get_name(),'origin':[b.origin.x,b.origin.y,b.origin.z],'size':[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z],'slots':slots}
    if name=='coastal_cliff_02':
     settings=mesh.get_editor_property('nanite_settings');settings.set_editor_property('enabled',True);mesh.set_editor_property('nanite_settings',settings);d['nanite_enabled']=True
    u.EditorAssetLibrary.save_loaded_asset(mesh);data['meshes'].append(d)
  out['assets'][name]=data
 out['passed']=True
except Exception:out['error']=traceback.format_exc();u.log_error(out['error'])
finally:open(os.path.join(T,'weapon_terrain_import.json'),'w').write(json.dumps(out,indent=2))
