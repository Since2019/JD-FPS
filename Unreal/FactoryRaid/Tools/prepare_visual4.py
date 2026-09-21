import unreal as u,os,json
T=os.path.dirname(__file__);P='/Game/Factory/Visual4';A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
tasks=[]
for file in os.listdir(os.path.join(T,'Visual4Source')):
    if not file.endswith('.obj'):continue
    task=u.AssetImportTask();task.filename=os.path.join(T,'Visual4Source',file);task.destination_path=P+'/Meshes';task.destination_name=os.path.splitext(file)[0];task.automated=True;task.save=True;task.replace_existing=True
    opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.static_mesh_import_data.set_editor_property('combine_meshes',True);opts.static_mesh_import_data.set_editor_property('auto_generate_collision',False);task.options=opts;tasks.append(task)
A.import_asset_tasks(tasks)
def expr(m,c):return M.create_material_expression(m,c)
def value(m,v,prop):
    e=expr(m,u.MaterialExpressionConstant3Vector if isinstance(v,tuple) else u.MaterialExpressionConstant)
    if isinstance(v,tuple):e.constant=u.LinearColor(*v,1)
    else:e.r=v
    M.connect_material_property(e,'',prop);return e
def custom(m,code,inputs,prop,scalar=False):
    e=expr(m,u.MaterialExpressionCustom);e.set_editor_property('code',code);e.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else u.CustomMaterialOutputType.CMOT_FLOAT3)
    entries=[]
    for n in inputs:i=u.CustomInput();i.set_editor_property('input_name',n);entries.append(i)
    e.set_editor_property('inputs',entries)
    for n,node in inputs.items():M.connect_material_expressions(node,'',e,n)
    M.connect_material_property(e,'',prop)
specs=[('M_Receiver',(.039,.047,.05),.52,0),('M_RIS',(.24,.16,.09),.55,0),('M_Hardware',(.08,.09,.095),.4,1),('M_Polymer',(.027,.031,.027),.72,0),('M_Dark',(.012,.014,.013),.86,0),('M_PMC_Helmet',(.23,.21,.14),.74,0),('M_FAST_Hardware',(.062,.059,.046),.65,0),('M_FAST_Loop',(.09,.085,.053),.93,0),('M_FAST_Straps',(.029,.032,.026),.86,0)]
for name,tint,rough,metal in specs:
    path=P+'/Materials/'+name;m=u.load_asset(path) or A.create_asset(name,P+'/Materials',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
    uv=expr(m,u.MaterialExpressionTextureCoordinate);c=value(m,tint,u.MaterialProperty.MP_BASE_COLOR)
    # No contact masks exist for this legacy geometry: do not invent wear.
    value(m,rough,u.MaterialProperty.MP_ROUGHNESS)
    value(m,(0.,0.,1.),u.MaterialProperty.MP_NORMAL)
    value(m,metal,u.MaterialProperty.MP_METALLIC);m.set_editor_property('two_sided',True);M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
# Keep scanned cloth maps; reduce oversized weave relief that previously looked like knit armour.
for name in ['M_PMC_Uniform','M_PMC_Coyote','M_PMC_Black']:
    target=P+'/Materials/'+name;m=u.load_asset(target) or u.EditorAssetLibrary.duplicate_asset('/Game/Factory/Visual3/Materials/'+name,target)
    for obj in u.ObjectIterator():
        if obj.get_outer()==m and isinstance(obj,u.MaterialExpressionCustom):
            code=obj.get_editor_property('code');code=code.replace('UV*1.5','UV*3.0').replace('n.xy*=.65','n.xy*=.22').replace('weave=clamp(dot(photo,float3(.3,.45,.25))*2.8,.72,1.22)','weave=clamp(dot(photo,float3(.3,.45,.25))*2.8,.86,1.12)');obj.set_editor_property('code',code)
    M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
open(os.path.join(T,'visual4_prepare.json'),'w').write(json.dumps({'ready':True,'helmet_meshes':4,'materials':12}));u.log('VISUAL4_READY')
u.log_warning('After legacy asset rebuild, run Tools/apply_realism.py to restore the approved physical material/light baseline.')
