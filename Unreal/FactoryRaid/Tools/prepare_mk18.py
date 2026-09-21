import unreal as u,os,json
T=os.path.dirname(__file__);S=os.path.join(T,'WeaponSource');P='/Game/Factory/Visual3';A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
tasks=[]
for file in os.listdir(S):
    if not file.endswith(('.jpg','.obj')):continue
    task=u.AssetImportTask();task.filename=os.path.join(S,file);task.destination_path=P+('/Meshes' if file.endswith('.obj') else '/Textures');task.destination_name=os.path.splitext(file)[0];task.automated=True;task.save=True;task.replace_existing=True
    if file.endswith('.obj'):
        opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.static_mesh_import_data.set_editor_property('combine_meshes',True);opts.static_mesh_import_data.set_editor_property('auto_generate_collision',False);task.options=opts
    tasks.append(task)
A.import_asset_tasks(tasks)
def mat(name):
    m=u.load_asset(P+'/Materials/'+name) or A.create_asset(name,P+'/Materials',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m);return m
def expr(m,c):return M.create_material_expression(m,c)
def value(m,v,prop):
    e=expr(m,u.MaterialExpressionConstant3Vector if isinstance(v,tuple) else u.MaterialExpressionConstant)
    if isinstance(v,tuple):e.constant=u.LinearColor(*v,1)
    else:e.r=v
    M.connect_material_property(e,'',prop);return e
def custom(m,code,inputs,prop,kind=u.CustomMaterialOutputType.CMOT_FLOAT3):
    e=expr(m,u.MaterialExpressionCustom);e.set_editor_property('output_type',kind);items=[]
    for name in inputs:
        i=u.CustomInput();i.set_editor_property('input_name',name);items.append(i)
    e.set_editor_property('inputs',items);e.set_editor_property('code',code)
    for name,node in inputs.items():M.connect_material_expressions(node,'',e,name)
    M.connect_material_property(e,'',prop);return e
def save(m):M.recompile_material(m);assert u.EditorAssetLibrary.save_loaded_asset(m)
for name,tint,rough,metal in [('M_Receiver',(.042,.049,.050),.54,.8),('M_RIS',(.24,.14,.066),.60,.65),('M_Polymer',(.044,.051,.044),.83,0.),('M_Hardware',(.045,.047,.042),.43,.85),('M_Dark',(.012,.014,.013),.92,0.)]:
    m=mat(name);uv=expr(m,u.MaterialExpressionTextureCoordinate);c=value(m,tint,u.MaterialProperty.MP_BASE_COLOR)
    custom(m,'return Tint;',{'UV':uv,'Tint':c},u.MaterialProperty.MP_BASE_COLOR)
    value(m,rough,u.MaterialProperty.MP_ROUGHNESS);value(m,metal,u.MaterialProperty.MP_METALLIC);m.set_editor_property('two_sided',True);save(m)
m=mat('M_HiddenTemplate');m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('used_with_skeletal_mesh',True);value(m,0.,u.MaterialProperty.MP_OPACITY_MASK);save(m)
textures={}
for channel in ['diff','rough','nor_dx']:
    t=u.load_asset(P+'/Textures/rough_linen_'+channel+'_1k');assert t
    t.set_editor_property('srgb',channel=='diff');t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT);u.EditorAssetLibrary.save_loaded_asset(t);textures[channel]=t
noise='''struct Noise {float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);} float n(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}} noise;'''
for name,tint,camo in [('M_PMC_Uniform',(.18,.22,.115),True),('M_PMC_Coyote',(.29,.205,.112),False),('M_PMC_Black',(.039,.045,.038),False)]:
    m=mat(name);uv=expr(m,u.MaterialExpressionTextureCoordinate);c=value(m,tint,u.MaterialProperty.MP_BASE_COLOR);nodes={}
    for channel,t in textures.items():e=expr(m,u.MaterialExpressionTextureObject);e.texture=t;nodes[channel]=e
    code=noise+'''float3 photo=Texture2DSample(Tex,TexSampler,UV*1.5).rgb;float weave=clamp(dot(photo,float3(.3,.45,.25))*2.8,.72,1.22);float dirt=noise.n(UV*22);float broad=noise.n(UV*7+noise.n(UV*15)*2);float3 base=Tint;'''
    if camo:code+='base=lerp(base,float3(.065,.080,.042),smoothstep(.55,.63,broad));base=lerp(base,float3(.30,.255,.145),smoothstep(.66,.72,noise.n(UV*9+8)));'
    code+='return base*weave*lerp(.84,1.08,dirt);'
    custom(m,code,{'UV':uv,'Tex':nodes['diff'],'Tint':c},u.MaterialProperty.MP_BASE_COLOR)
    custom(m,'float3 n=Texture2DSample(Tex,TexSampler,UV*1.5).rgb*2-1;n.xy*=.65;return normalize(n);',{'UV':uv,'Tex':nodes['nor_dx']},u.MaterialProperty.MP_NORMAL)
    custom(m,'return clamp(Texture2DSample(Tex,TexSampler,UV*1.5).r,.68,.96);',{'UV':uv,'Tex':nodes['rough']},u.MaterialProperty.MP_ROUGHNESS,u.CustomMaterialOutputType.CMOT_FLOAT1)
    value(m,0.,u.MaterialProperty.MP_METALLIC);m.set_editor_property('used_with_skeletal_mesh',True);m.set_editor_property('two_sided',True);save(m)
m=mat('M_PMC_Helmet');value(m,(.14,.17,.095),u.MaterialProperty.MP_BASE_COLOR);value(m,.81,u.MaterialProperty.MP_ROUGHNESS);value(m,.08,u.MaterialProperty.MP_METALLIC);save(m)
# Read-only local API metadata for trigger mapping and native socket coordinates.
ctx=u.load_asset('/Game/Variant_Shooter/Input/IMC_Weapons');mesh=u.load_asset('/Game/Weapons/Rifle/Meshes/SKM_Rifle');report={'complete':True}
input_path=P+'/Input/IMC_TacticalWeapons'
input_context=u.load_asset(input_path) or u.EditorAssetLibrary.duplicate_asset('/Game/Variant_Shooter/Input/IMC_Weapons',input_path)
input_context.unmap_all_keys_from_action(u.load_asset('/Game/Variant_Shooter/Input/Actions/IA_Shoot'))
assert u.EditorAssetLibrary.save_loaded_asset(input_context)
report['muzzle_socket']=str(mesh.find_socket_info('Muzzle'))
report['mapping_methods']={n:str(getattr(ctx,n).__doc__) for n in dir(ctx) if 'unmap' in n}
report['socket_methods']={n:str(getattr(mesh,n).__doc__) for n in dir(mesh) if 'socket' in n}
report['rebuild_methods']={n:str(getattr(u.EnhancedInputLibrary,n).__doc__) for n in dir(u.EnhancedInputLibrary) if 'rebuild' in n}
open(os.path.join(T,'mk18_prepare.json'),'w').write(json.dumps(report,indent=2))
u.log('MK18_ASSETS_READY')
