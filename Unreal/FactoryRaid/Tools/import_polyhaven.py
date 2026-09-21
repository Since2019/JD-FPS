import unreal as u,os,json,traceback
T=os.path.dirname(__file__);A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
report={'assets':[],'passed':False}
def imp(path,dest,name,mesh=False):
    task=u.AssetImportTask();task.filename=path;task.destination_path=dest;task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
    if mesh:
        opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False
        opt.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opt.set_editor_property('automated_import_should_detect_type',False)
        opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=True
        task.options=opt
    A.import_asset_tasks([task]);objs=[u.load_asset(p) for p in task.imported_object_paths];assert objs,(path,task.imported_object_paths)
    return next(x for x in objs if isinstance(x,u.StaticMesh if mesh else u.Texture2D))
try:
    for item in json.load(open(os.path.join(T,'PolyHavenSource','manifest.json'))):
        name=item['id'];dest='/Game/Realism/PolyHaven/'+name;mesh=imp(item['files']['mesh']['path'],dest,'SM_'+name,True)
        mat=u.load_asset(dest+'/M_'+name) or A.create_asset('M_'+name,dest,u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(mat)
        textures={};props={'Diffuse':u.MaterialProperty.MP_BASE_COLOR,'nor_dx':u.MaterialProperty.MP_NORMAL,'Rough':u.MaterialProperty.MP_ROUGHNESS,'Metal':u.MaterialProperty.MP_METALLIC,'AO':u.MaterialProperty.MP_AMBIENT_OCCLUSION,'Alpha':u.MaterialProperty.MP_OPACITY_MASK}
        for channel,p in props.items():
            if channel not in item['files']:continue
            tex=imp(item['files'][channel]['path'],dest,'T_'+channel)
            tex.set_editor_property('srgb',channel=='Diffuse')
            tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if channel=='nor_dx' else u.TextureCompressionSettings.TC_DEFAULT if channel=='Diffuse' else u.TextureCompressionSettings.TC_MASKS)
            tex.set_editor_property('filter',u.TextureFilter.TF_DEFAULT);u.EditorAssetLibrary.save_loaded_asset(tex)
            node=M.create_material_expression(mat,u.MaterialExpressionTextureSample);node.texture=tex
            node.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL if channel=='nor_dx' else u.MaterialSamplerType.SAMPLERTYPE_COLOR if channel=='Diffuse' else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
            M.connect_material_property(node,'RGB' if channel in ['Diffuse','nor_dx'] else 'R',p)
            textures[channel]=tex.get_path_name()
        if 'Alpha' in textures:mat.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
        M.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
        for slot in range(len(mesh.get_editor_property('static_materials'))):mesh.set_material(slot,mat)
        u.EditorAssetLibrary.save_loaded_asset(mesh)
        b=mesh.get_bounds();report['assets'].append({'id':name,'mesh':mesh.get_path_name(),'dimensions_cm':[b.box_extent.x*2,b.box_extent.y*2,b.box_extent.z*2],'origin_cm':[b.origin.x,b.origin.y,b.origin.z],'source_polycount':item['info']['polycount'],'textures':textures,'material_slots':len(mesh.get_editor_property('static_materials'))})
    report['passed']=True
except Exception:report['error']=traceback.format_exc();u.log_error(report['error'])
finally:open(os.path.join(T,'polyhaven_import.json'),'w').write(json.dumps(report,indent=2))


