"""Auditable realism baseline; no procedural edge wear or destructive map rebuild."""
import unreal as u,os,json,shutil,time
T=os.path.dirname(__file__);ROOT=os.path.dirname(T);M=u.MaterialEditingLibrary;A=u.AssetToolsHelpers.get_asset_tools()
BACK=os.path.join(T,'RealismBackup');report={'materials':[],'maps':{},'backup':BACK}
def backup(path):
    rel=path.split('.')[0].replace('/Game/','',1)+('.umap' if '/Maps/' in path else '.uasset')
    src=os.path.join(ROOT,'Content',rel);dst=os.path.join(BACK,rel)
    if os.path.isfile(src) and not os.path.exists(dst):os.makedirs(os.path.dirname(dst),exist_ok=True);shutil.copy2(src,dst)
def expr(m,c):return M.create_material_expression(m,c)
def value(m,v,prop):
    e=expr(m,u.MaterialExpressionConstant3Vector if isinstance(v,tuple) else u.MaterialExpressionConstant)
    if isinstance(v,tuple):e.constant=u.LinearColor(*v,1)
    else:e.r=v
    M.connect_material_property(e,'',prop);return e
def custom(m,code,nodes,prop,scalar=True):
    e=expr(m,u.MaterialExpressionCustom);e.set_editor_property('code',code);e.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else u.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs=[]
    for name in nodes:i=u.CustomInput();i.set_editor_property('input_name',name);inputs.append(i)
    e.set_editor_property('inputs',inputs)
    for name,node in nodes.items():M.connect_material_expressions(node,'',e,name)
    M.connect_material_property(e,'',prop);return e
def save(m):M.recompile_material(m);assert u.EditorAssetLibrary.save_loaded_asset(m)
def surface(path,color,rough,metal):
    m=u.load_asset(path)
    if not m:return
    backup(path);M.delete_all_material_expressions(m)
    value(m,color,u.MaterialProperty.MP_BASE_COLOR);value(m,rough,u.MaterialProperty.MP_ROUGHNESS);value(m,metal,u.MaterialProperty.MP_METALLIC);value(m,1.,u.MaterialProperty.MP_AMBIENT_OCCLUSION)
    # Low-amplitude microfinish, in real centimetres. This is not a wear mask.
    p=expr(m,u.MaterialExpressionWorldPosition)
    custom(m,'return clamp(R + .012*sin(P.x*22)*sin(P.y*27)*sin(P.z*19),0,1);',{'P':p,'R':value(m,rough,u.MaterialProperty.MP_ROUGHNESS)},u.MaterialProperty.MP_ROUGHNESS)
    save(m);report['materials'].append({'path':path,'roughness':[round(rough-.012,3),round(rough+.012,3)],'metallic':metal,'wear':'none; no authored contact mask available'})
for name,color,r,mt in [('M_Receiver',(.039,.047,.05),.52,0),('M_RIS',(.24,.16,.09),.55,0),('M_Hardware',(.08,.09,.095),.4,1),('M_Polymer',(.027,.031,.027),.72,0),('M_Dark',(.012,.014,.013),.86,0),('M_PMC_Helmet',(.23,.21,.14),.74,0),('M_FAST_Hardware',(.062,.059,.046),.65,0),('M_FAST_Loop',(.09,.085,.053),.93,0),('M_FAST_Straps',(.029,.032,.026),.86,0)]:surface('/Game/Factory/Visual4/Materials/'+name,color,r,mt)
for name,color,r,mt in [('steel',(.14,.17,.18),.48,1),('rust',(.22,.10,.042),.88,0),('green',(.16,.22,.13),.64,0),('yellow',(.54,.34,.055),.62,0),('dark',(.035,.043,.043),.72,0),('paper',(.48,.46,.38),.9,0),('red',(.31,.065,.038),.62,0),('blue',(.08,.18,.22),.62,0)]:surface('/Game/Factory/Visual2/Materials/M_'+name,color,r,mt)
for name,color,r,mt in [('Hull',(.30,.055,.018),.67,0),('White',(.52,.58,.57),.65,0),('Dark',(.022,.032,.037),.68,0),('Steel',(.25,.29,.30),.46,1),('Yellow',(.68,.35,.035),.62,0),('Blue',(.065,.14,.17),.66,0),('Rubber',(.014,.018,.02),.88,0),('Water',(.012,.035,.045),.16,0),('Green',(.045,.18,.13),.65,0)]:surface('/Game/Icebreaker/Materials/M_'+name,color,r,mt)
# Preserve scanned cloth and its UVs; reduce the old broad contrast and weave relief.
for name in ['M_PMC_Uniform','M_PMC_Coyote','M_PMC_Black']:
    path='/Game/Factory/Visual4/Materials/'+name;m=u.load_asset(path);backup(path)
    for e in u.ObjectIterator():
        if e.get_outer()==m and isinstance(e,u.MaterialExpressionCustom):
            code=e.get_editor_property('code').replace('n.xy*=.22','n.xy*=.10').replace('lerp(.84,1.08,dirt)','lerp(.97,1.02,dirt)');e.set_editor_property('code',code)
    save(m)
# Correct imported data texture interpretation without replacing the authored UV work.
for folder in ['HK416','EOTechXPS3Scope']:
    for path in u.EditorAssetLibrary.list_assets('/Game/Game/Assets/Models/Weapons/'+folder):
        a=u.load_asset(path)
        if isinstance(a,u.Texture2D):
            backup(path);name=a.get_name();a.set_editor_property('srgb','BaseColor' in name or 'Base_Color' in name)
            if 'Normal' in name:a.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
            u.EditorAssetLibrary.save_loaded_asset(a)
# Roughness remains spatially varied by each imported map; no added random scratches.
for folder,mat,tex,lo,hi in [('HK416','Low','HK416RoughnessLow2k',.4,.85),('HK416','Sights','HK416RoughnessSights',.45,.85),('EOTechXPS3Scope','EOTechXPS3Mat','EotechXPS_Roughness',.46,.82)]:
    path='/Game/Game/Assets/Models/Weapons/'+folder+'/'+mat;m=u.load_asset(path);backup(path)
    # These visible groups are coated exteriors. A later authored material-ID mask
    # is required before exposing separate bare fasteners; avoid all-over metal.
    value(m,0.,u.MaterialProperty.MP_METALLIC)
    t=expr(m,u.MaterialExpressionTextureObject);t.texture=u.load_asset('/Game/Game/Assets/Models/Weapons/'+folder+'/'+tex);uv=expr(m,u.MaterialExpressionTextureCoordinate)
    custom(m,'return clamp(Texture2DSample(T,TSampler,UV).r,%s,%s);'%(lo,hi),{'T':t,'UV':uv},u.MaterialProperty.MP_ROUGHNESS);save(m)
    for e in u.ObjectIterator():
        if e.get_outer()==m and isinstance(e,u.MaterialExpressionTextureSample):
            tex=e.get_editor_property('texture')
            if tex:
                sampler=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if tex.get_editor_property('compression_settings')==u.TextureCompressionSettings.TC_NORMALMAP else u.MaterialSamplerType.SAMPLERTYPE_COLOR if tex.get_editor_property('srgb') else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
                e.set_editor_property('sampler_type',sampler)
    save(m)
# Small, specifically placed service stains. Mask describes one deposit, not noise.
path='/Game/Realism/M_ServiceOil';oil=u.load_asset(path) or A.create_asset('M_ServiceOil','/Game/Realism',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(oil)
oil.set_editor_property('material_domain',u.MaterialDomain.MD_DEFERRED_DECAL);oil.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
uv=expr(oil,u.MaterialExpressionTextureCoordinate)
custom(oil,'float2 q=(UV-.5)*2;float a=length(q/float2(.82,.64));float b=length((q-float2(.3,.12))/float2(.48,.34));return .42*(1-smoothstep(.7,1,min(a,b)));',{'UV':uv},u.MaterialProperty.MP_OPACITY)
value(oil,(.026,.024,.018),u.MaterialProperty.MP_BASE_COLOR);value(oil,.31,u.MaterialProperty.MP_ROUGHNESS);value(oil,0.,u.MaterialProperty.MP_METALLIC);save(oil)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
for map_path in ['/Game/Factory/Maps/ClassicFactoryVisual','/Game/Icebreaker/Maps/Icebreaker']:
    backup(map_path);L.load_level(map_path);ice='Icebreaker' in map_path;data={'lights':[],'scale_samples':[],'service_stains':0}
    actors=list(E.get_all_level_actors())
    for a in actors:
        if a.actor_has_tag('RealismServiceStain'):E.destroy_actor(a);continue
        if isinstance(a,u.PostProcessVolume):
            s=a.get_editor_property('settings')
            for key,val in [('override_bloom_intensity',True),('bloom_intensity',.035),('override_auto_exposure_bias',True),('auto_exposure_bias',-.35 if ice else -.2),('override_auto_exposure_speed_up',True),('auto_exposure_speed_up',2.),('override_auto_exposure_speed_down',True),('auto_exposure_speed_down',1.),('override_color_saturation',True),('color_saturation',u.Vector4(.95,.95,.95,1)),('override_motion_blur_amount',True),('motion_blur_amount',0.)]:s.set_editor_property(key,val)
            a.set_editor_property('settings',s)
        if isinstance(a,(u.PointLight,u.SpotLight)):
            c=a.light_component;old=c.intensity;power=old
            if ice and a.get_actor_location().z<320:power=min(old,6000.)
            c.set_intensity(power);c.set_editor_property('indirect_lighting_intensity',1.);c.set_editor_property('source_radius',12.)
            data['lights'].append({'label':a.get_actor_label(),'old':old,'new':power})
        if isinstance(a,u.StaticMeshActor):
            label=a.get_actor_label()
            if any(k in label.lower() for k in ['door','locker','table','skid','rail']):
                origin,extent=a.get_actor_bounds(False);data['scale_samples'].append({'label':label,'center_cm':[origin.x,origin.y,origin.z],'aabb_cm':[2*extent.x,2*extent.y,2*extent.z]})
            if label=='Diesel generator skid':
                pos=a.get_actor_location();stain=E.spawn_actor_from_class(u.DecalActor,u.Vector(pos.x-310,pos.y+(150 if pos.y>0 else -150),12),u.Rotator(pitch=-90));stain.set_actor_label('Localized oil at generator service coupling');stain.tags=[u.Name('RealismServiceStain')];stain.decal.set_decal_material(oil);stain.decal.set_editor_property('decal_size',u.Vector(20,22,14));data['service_stains']+=1
    assert L.save_current_level();report['maps'][map_path]=data
open(os.path.join(T,'realism_apply.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2));u.log('REALISM_BASELINE_SAVED')
