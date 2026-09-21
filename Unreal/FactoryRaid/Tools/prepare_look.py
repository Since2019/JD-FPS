"""Idempotent lighting, scanned surfaces, optic and cloth presentation upgrade."""
import unreal as u,os,json
T=os.path.dirname(__file__);A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
V='/Game/Factory/Visual2'
tasks=[]
for file in os.listdir(os.path.join(T,'SurfaceSource')):
    if not file.endswith('_1k.jpg'):continue
    task=u.AssetImportTask();task.filename=os.path.join(T,'SurfaceSource',file);task.destination_path='/Game/Factory/Surfaces';task.destination_name=os.path.splitext(file)[0];task.automated=True;task.save=True;task.replace_existing=True;tasks.append(task)
for name in ['OPT_Housing','OPT_Hardware','OPT_Reticle','PMC_Seams','PMC_Buckles','PMC_Radio','PMC_UtilityPouch','PMC_Zipper','PMC_FabricLimb']:
    task=u.AssetImportTask();task.filename=os.path.join(T,'PresentationSource',name+'.obj');task.destination_path=V+'/PMC';task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
    opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.static_mesh_import_data.set_editor_property('combine_meshes',True);opts.static_mesh_import_data.set_editor_property('auto_generate_collision',False);task.options=opts;tasks.append(task)
A.import_asset_tasks(tasks)
def mat(path):
    path=path.replace('/Game/Factory/Materials',V+'/Materials').replace('/Game/Factory/PMC',V+'/PMC').replace('/Game/Factory/Optics',V+'/Optics')
    m=u.load_asset(path) or A.create_asset(path.split('/')[-1],path.rsplit('/',1)[0],u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m);return m
def constant(m,value,prop):
    if isinstance(value,tuple):e=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);e.constant=u.LinearColor(*value,1)
    else:e=M.create_material_expression(m,u.MaterialExpressionConstant);e.r=value
    M.connect_material_property(e,'',prop);return e
def expr(m,cls):return M.create_material_expression(m,cls)
def custom(m,code,inputs,prop,kind=u.CustomMaterialOutputType.CMOT_FLOAT3):
    e=expr(m,u.MaterialExpressionCustom);e.set_editor_property('output_type',kind);items=[]
    for name,node in inputs.items():
        item=u.CustomInput();item.set_editor_property('input_name',name);items.append(item)
    e.set_editor_property('inputs',items);e.set_editor_property('code',code)
    for name,node in inputs.items():M.connect_material_expressions(node,'',e,name)
    M.connect_material_property(e,'',prop);return e
def finish(m):M.recompile_material(m);assert u.EditorAssetLibrary.save_loaded_asset(m)

for material,asset,scale,tint in [('wall','concrete_wall_006',240.,.88),('floor','concrete_floor_02',300.,.80)]:
    m=mat('/Game/Factory/Materials/M_'+material);m.set_editor_property('tangent_space_normal',False)
    pos=expr(m,u.MaterialExpressionWorldPosition);normal=expr(m,u.MaterialExpressionVertexNormalWS)
    textures={}
    for channel in ['diff','rough','nor_dx']:
        texture=u.load_asset('/Game/Factory/Surfaces/'+asset+'_'+channel+'_1k');texture.set_editor_property('srgb',channel=='diff')
        # Store raw signed-normal encoded RGB; the custom triplanar shader decodes it.
        texture.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT);u.EditorAssetLibrary.save_loaded_asset(texture)
        obj=expr(m,u.MaterialExpressionTextureObject);obj.texture=texture;textures[channel]=obj
    prefix='float3 w=pow(abs(N),8);w/=max(dot(w,1),0.001);float3 p=Pos/%f;'%scale
    for channel,prop in [('diff',u.MaterialProperty.MP_BASE_COLOR),('rough',u.MaterialProperty.MP_ROUGHNESS)]:
        code=prefix+'float3 v=Texture2DSample(Tex,TexSampler,p.yz).rgb*w.x+Texture2DSample(Tex,TexSampler,p.xz).rgb*w.y+Texture2DSample(Tex,TexSampler,p.xy).rgb*w.z;'
        code+=('return v*%f*(0.95+0.05*sin(Pos.x*.0018+sin(Pos.y*.0014)));'%tint if channel=='diff' else 'return clamp(v.r,0.62,0.98);')
        custom(m,code,{'Tex':textures[channel],'Pos':pos,'N':normal},prop,u.CustomMaterialOutputType.CMOT_FLOAT3 if channel=='diff' else u.CustomMaterialOutputType.CMOT_FLOAT1)
    code=prefix+'float3 a=Texture2DSample(Tex,TexSampler,p.yz).xyz*2-1;float3 b=Texture2DSample(Tex,TexSampler,p.xz).xyz*2-1;float3 c=Texture2DSample(Tex,TexSampler,p.xy).xyz*2-1;a.xy*=0.4;b.xy*=0.4;c.xy*=0.4;return normalize(float3(sign(N.x)*a.z,a.x,a.y)*w.x+float3(b.x,sign(N.y)*b.z,b.y)*w.y+float3(c.x,c.y,sign(N.z)*c.z)*w.z);'
    custom(m,code,{'Tex':textures['nor_dx'],'Pos':pos,'N':normal},u.MaterialProperty.MP_NORMAL);constant(m,0.,u.MaterialProperty.MP_METALLIC);finish(m)

palette={'steel':(.14,.17,.18),'rust':(.22,.10,.042),'green':(.16,.22,.13),'yellow':(.54,.34,.055),'dark':(.035,.043,.043),'paper':(.48,.46,.38),'red':(.31,.065,.038),'blue':(.08,.18,.22)}
for name,tint in palette.items():
    m=mat('/Game/Factory/Materials/M_'+name);p=expr(m,u.MaterialExpressionWorldPosition);c=constant(m,tint,u.MaterialProperty.MP_BASE_COLOR)
    constant(m,.88 if name=='rust' else .90 if name=='paper' else .48 if name=='steel' else .64,u.MaterialProperty.MP_ROUGHNESS)
    constant(m,1. if name=='steel' else 0.,u.MaterialProperty.MP_METALLIC);finish(m)

for name,tint in [('M_PMC_Uniform',(.16,.20,.105)),('M_PMC_Coyote',(.26,.195,.105)),('M_PMC_Black',(.034,.039,.034))]:
    m=mat('/Game/Factory/PMC/'+name);uv=expr(m,u.MaterialExpressionTextureCoordinate);c=constant(m,tint,u.MaterialProperty.MP_BASE_COLOR)
    custom(m,'float2 p=UV*5;float n=sin(p.x*1.7+sin(p.y*2.1))*sin(p.y*2.9+sin(p.x*2.5));float n2=sin(p.x*5.3+p.y*3.3+sin(p.y*6.1));float patch=smoothstep(.1,.45,n+.2*n2);float weave=.965+.035*sin(UV.x*950)*sin(UV.y*950);return Tint*lerp(.66,1.17,patch)*weave;',{'UV':uv,'Tint':c},u.MaterialProperty.MP_BASE_COLOR)
    custom(m,'float2 w=float2(sin(UV.x*950),sin(UV.y*950))*.085;return normalize(float3(w,1));',{'UV':uv},u.MaterialProperty.MP_NORMAL)
    constant(m,.88,u.MaterialProperty.MP_ROUGHNESS);constant(m,0.,u.MaterialProperty.MP_METALLIC);m.set_editor_property('used_with_skeletal_mesh',True);m.set_editor_property('two_sided',True);finish(m)
for name,color,rough,metal in [('M_OpticBody',(.065,.073,.058),.66,.25),('M_OpticMetal',(.026,.030,.025),.42,.7)]:
    m=mat('/Game/Factory/Optics/'+name);constant(m,color,u.MaterialProperty.MP_BASE_COLOR);constant(m,rough,u.MaterialProperty.MP_ROUGHNESS);constant(m,metal,u.MaterialProperty.MP_METALLIC);m.set_editor_property('two_sided',True);finish(m)
m=mat('/Game/Factory/Optics/M_SpecterReticle');m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('two_sided',True);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
uv=expr(m,u.MaterialExpressionTextureCoordinate)
# Authored CX5395-style dual-thickness crosshair, BDC bars/circles, range ladder.
reticle='''float2 p=(.5-UV)*2;float r=length(p);float ink=0;
ink=max(ink,(1-step(.010,abs(p.y)))*step(.12,abs(p.x))*step(abs(p.x),.91));
ink=max(ink,(1-step(.004,abs(p.x)))*step(.08,p.y)*step(p.y,.79));
ink=max(ink,(1-step(.010,abs(p.x)))*step(.26,-p.y)*step(-p.y,.91));
for(int i=0;i<4;i++){float y=.12+i*.095;float w=.105-i*.018;ink=max(ink,(1-step(.005,abs(p.y-y)))*step(abs(p.x),w));}
for(int j=0;j<3;j++){float2 q=p-float2(0,.57+j*.085);ink=max(ink,1-step(.004,abs(length(q)-(.043-j*.006))));}
ink=max(ink,(1-step(.004,abs(p.y-.40)))*step(-.76,p.x)*step(p.x,-.39));
for(int k=0;k<4;k++){float x=-.74+k*.10;ink=max(ink,(1-step(.004,abs(p.x-x)))*step(.40-(.20-k*.035),p.y)*step(p.y,.40));}
ink=max(ink,1-step(.012,r));return ink*step(r,.965);'''
custom(m,reticle,{'UV':uv},u.MaterialProperty.MP_OPACITY_MASK,u.CustomMaterialOutputType.CMOT_FLOAT1)
custom(m,'float d=length((UV-.5)*2);return d<.016?float3(.85,.025,.008):float3(.004,.004,.004);',{'UV':uv},u.MaterialProperty.MP_EMISSIVE_COLOR);finish(m)

m=mat('/Game/Factory/Optics/M_SpecterLens');m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('two_sided',True);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
uv=expr(m,u.MaterialExpressionTextureCoordinate);texture=expr(m,u.MaterialExpressionTextureObjectParameter);texture.set_editor_property('parameter_name','ScopeView');texture.set_editor_property('texture',u.load_asset('/Engine/EngineResources/WhiteSquareTexture'))
custom(m,'return 1-step(.994,length((UV-.5)*2));',{'UV':uv},u.MaterialProperty.MP_OPACITY_MASK,u.CustomMaterialOutputType.CMOT_FLOAT1)
lenscode=reticle.replace('return ink*step(r,.965);','float3 scene=Texture2DSample(View,ViewSampler,1-UV).rgb;float vignette=1-.20*smoothstep(.70,.99,r);float3 inkColor=r<.016?float3(.55,.012,.003):float3(.001,.001,.001);return lerp(scene*vignette,inkColor,ink);')
custom(m,lenscode,{'UV':uv,'View':texture},u.MaterialProperty.MP_EMISSIVE_COLOR);finish(m)

L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryTactical');E=u.get_editor_subsystem(u.EditorActorSubsystem);lights=[]
for a in E.get_all_level_actors():
    if isinstance(a,u.StaticMeshActor):
        c=a.static_mesh_component
        for i in range(c.get_num_materials()):
            old=c.get_material(i)
            if old:
                replacement=u.load_asset(V+'/Materials/'+old.get_name())
                if replacement:c.set_material(i,replacement)
    elif isinstance(a,(u.PointLight,u.SpotLight)):
        c=a.light_component;z=a.get_actor_location().z
        c.set_editor_property('intensity_units',u.LightUnits.LUMENS)
        if isinstance(a,u.SpotLight):power=95000.;radius=3500.
        elif z>700:power=18000.;radius=2300.
        elif z<0:power=3300.;radius=1250.
        else:power=5000.;radius=1350.
        c.set_intensity(power);c.set_editor_property('attenuation_radius',radius);c.set_editor_property('source_radius',18.);c.set_editor_property('indirect_lighting_intensity',1.4)
        lights.append({'name':a.get_actor_label(),'lumens':power,'radius':radius})
    elif isinstance(a,u.PostProcessVolume):
        s=a.get_editor_property('settings')
        for key,val in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_HISTOGRAM),('override_auto_exposure_min_brightness',True),('auto_exposure_min_brightness',1.),('override_auto_exposure_max_brightness',True),('auto_exposure_max_brightness',7.),('override_auto_exposure_bias',True),('auto_exposure_bias',-.3),('override_auto_exposure_speed_up',True),('auto_exposure_speed_up',3.),('override_auto_exposure_speed_down',True),('auto_exposure_speed_down',1.5),('override_motion_blur_amount',True),('motion_blur_amount',0.),('override_bloom_intensity',True),('bloom_intensity',.12)]:s.set_editor_property(key,val)
        a.set_editor_property('settings',s)
    elif isinstance(a,u.ExponentialHeightFog):a.component.set_editor_property('fog_density',.002)
assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'/Game/Factory/Maps/ClassicFactoryVisual')
open(os.path.join(T,'look_prepare.json'),'w').write(json.dumps({'lights':lights,'completed':True},indent=2))
u.log('LOOK_UPGRADE_SAVED')


