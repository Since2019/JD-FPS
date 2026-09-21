"""Rebuild the authored classic-factory approximation in Unreal Editor."""
import unreal as u
import json, os, random, math

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'factory_layout.json'), encoding='utf-8'))
E = u.get_editor_subsystem(u.EditorActorSubsystem)
L = u.get_editor_subsystem(u.LevelEditorSubsystem)
A = u.AssetToolsHelpers.get_asset_tools()
M = u.MaterialEditingLibrary
BASE = '/Game/Factory'

def cv(p, scale=100):
    return u.Vector(p[0]*scale, -p[2]*scale, p[1]*scale)

def material(name, color, metallic=0, rough=.8, texture=None, glow=False):
    path = BASE + '/Materials'
    existing = u.load_asset(path+'/'+name)
    m = existing or A.create_asset(name, path, u.Material, u.MaterialFactoryNew())
    if existing: M.delete_all_material_expressions(m)
    c = M.create_material_expression(m, u.MaterialExpressionConstant3Vector)
    c.set_editor_property('constant', u.LinearColor(*color,1))
    M.connect_material_property(c, '', u.MaterialProperty.MP_BASE_COLOR)
    if texture:
        obj = M.create_material_expression(m,u.MaterialExpressionTextureObject)
        obj.set_editor_property('texture',texture)
        pos = M.create_material_expression(m,u.MaterialExpressionWorldPosition)
        normal = M.create_material_expression(m,u.MaterialExpressionVertexNormalWS)
        code = M.create_material_expression(m,u.MaterialExpressionCustom)
        code.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
        inputs=[]
        for n in ['Tex','Pos','N','Tint']:
            item=u.CustomInput(); item.set_editor_property('input_name',n); inputs.append(item)
        code.set_editor_property('inputs',inputs)
        code.set_editor_property('code','float3 w=pow(abs(N),4);w/=max(dot(w,1),0.001);float3 p=Pos/220;return Tint*(Texture2DSample(Tex,TexSampler,p.yz).rgb*w.x+Texture2DSample(Tex,TexSampler,p.xz).rgb*w.y+Texture2DSample(Tex,TexSampler,p.xy).rgb*w.z);')
        for expr,n in [(obj,'Tex'),(pos,'Pos'),(normal,'N'),(c,'Tint')]: M.connect_material_expressions(expr,'',code,n)
        M.connect_material_property(code,'',u.MaterialProperty.MP_BASE_COLOR)
    for value,prop in [(metallic,u.MaterialProperty.MP_METALLIC),(rough,u.MaterialProperty.MP_ROUGHNESS)]:
        e=M.create_material_expression(m,u.MaterialExpressionConstant);e.set_editor_property('r',value);M.connect_material_property(e,'',prop)
    if glow:
        M.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(m)
    u.EditorAssetLibrary.save_loaded_asset(m)
    return m

def import_file(filename, path, name):
    existing=u.load_asset(path+'/'+name)
    if existing:return existing
    task=u.AssetImportTask();task.set_editor_property('filename',filename);task.set_editor_property('destination_path',path);task.set_editor_property('destination_name',name);task.set_editor_property('automated',True);task.set_editor_property('save',True)
    A.import_asset_tasks([task])
    return u.load_asset(path+'/'+name)

texture=import_file(os.path.abspath(os.path.join(HERE,'../../../assets/textures/weathered_concrete.png')),BASE+'/Textures','T_Concrete')
palette={'wall':(.65,.62,.53),'floor':(.44,.43,.39),'steel':(.12,.16,.17),'rust':(.32,.16,.075),'green':(.18,.26,.20),'yellow':(.65,.43,.075),'dark':(.045,.055,.055),'paper':(.62,.61,.53),'red':(.35,.08,.045),'blue':(.10,.24,.29)}
MAT={k:material('M_'+k,v,0 if k in ['wall','floor','paper'] else .55, .87 if k in ['wall','floor'] else .57,texture) for k,v in palette.items()}
MAT['light']=material('M_Luminous',(4.8,5.0,4.2),glow=True)
cube=u.load_asset('/Engine/BasicShapes/Cube.Cube')
cylinder=u.load_asset('/Engine/BasicShapes/Cylinder.Cylinder')
if u.EditorAssetLibrary.does_asset_exist('/Game/Factory/Maps/ClassicFactory'):
    L.load_level('/Game/Factory/Maps/ClassicFactory')
    for old in E.get_all_level_actors():
        if not isinstance(old,(u.WorldSettings,u.LevelScriptActor)):
            E.destroy_actor(old)
else:
    L.new_level('/Game/Factory/Maps/ClassicFactory')

def shape(label,pos,size,mat='steel',mesh=None,rotation=None,solid=True,tags=None):
    actor=E.spawn_actor_from_class(u.StaticMeshActor,pos,rotation or u.Rotator())
    actor.set_actor_label(label)
    comp=actor.static_mesh_component
    comp.set_static_mesh(mesh or cube)
    comp.set_material(0,MAT[mat])
    comp.set_collision_profile_name('BlockAll' if solid else 'NoCollision')
    actor.set_actor_scale3d(size)
    if tags:actor.set_editor_property('tags',tags)
    return actor

for i,d in enumerate(DATA['meshes']):
    rotation=u.MathLibrary.make_rot_from_xz(cv(d['basis_x'],1),cv(d['basis_y'],1))
    sz=d['size']
    actor=shape(d['name'],cv(d['position']),u.Vector(sz[0],sz[2],sz[1]),'light' if d['emission'] else d['material'],cylinder if d['shape']=='cylinder' else cube,rotation,d['solid'])
    if i%200==0:u.log('Factory geometry %d/%d'%(i,len(DATA['meshes'])))

# Doors carry gameplay tags. Native mode rotates the leaf around its hinge.
for i,d in enumerate(DATA['doors']):
    p=cv(d['position']); yaw=d['rotation'][1]
    rot=u.Rotator(0,yaw,0)
    actor=shape('Door | '+d['title'],p,u.Vector(1.5,.09,2.4),'green',rotation=rot,tags=['Door','Locked' if d['locked'] else 'Unlocked'])
    # Geometry initially sits open so the map remains traversable in the blueprint preview.
    actor.static_mesh_component.set_collision_profile_name('NoCollision')
    actor.set_actor_hidden_in_game(True)

for i,d in enumerate(DATA['loot']):
    marker=E.spawn_actor_from_class(u.TargetPoint,cv(d['position']))
    marker.set_actor_label('Loot | '+d['title'])
    marker.set_editor_property('tags',['Loot',str(i),d['item']])
for d in DATA['exits']:
    marker=E.spawn_actor_from_class(u.TargetPoint,cv(d['position']))
    marker.set_actor_label('Extract | '+d['title'])
    marker.set_editor_property('tags',['Extract',d['title'],'Key' if d['key'] else 'Free'])
for p in DATA['enemies']:
    marker=E.spawn_actor_from_class(u.TargetPoint,cv(p)+u.Vector(0,0,96))
    marker.set_editor_property('tags',['EnemySpawn'])

for d in DATA['lights']:
    actor=E.spawn_actor_from_class(u.SpotLight if d['spot'] else u.PointLight,cv(d['position']),u.Rotator(-90,0,0))
    c=actor.light_component
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units',u.LightUnits.LUMENS)
    c.set_intensity(d['energy']*(16000 if d['spot'] else 1600))
    c.set_light_color(u.LinearColor(*d['color'],1))
    c.set_editor_property('attenuation_radius',d['range']*100)
    c.set_cast_shadows(True)
    if d['spot']:c.set_editor_property('outer_cone_angle',67)

# Photographic light shafts and restrained exposure, without an outdoor sky washing out interiors.
pp=E.spawn_actor_from_class(u.PostProcessVolume,u.Vector())
pp.set_editor_property('unbound',True)
s=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',7.8),('override_motion_blur_amount',True),('motion_blur_amount',0.0),('override_bloom_intensity',True),('bloom_intensity',.22)]:
    s.set_editor_property(k,v)
pp.set_editor_property('settings',s)
fog=E.spawn_actor_from_class(u.ExponentialHeightFog,u.Vector(0,0,-150))
fog.component.set_editor_property('fog_density',.006)
fog.component.set_editor_property('enable_volumetric_fog',True)
fog.component.set_editor_property('volumetric_fog_scattering_distribution',.65)

# Additional construction details: wall skirting, conduit, base plates, tank fittings and rubbish.
rng=random.Random(4107)
for x in [-3000,-1400,1000,2400]:
    for y in [-2400,-800,800,2400]:
        shape('Steel column base plate',u.Vector(x,y,5),u.Vector(.8,.85,.1))
        for dx in [-27,27]:
            for dy in [-30,30]:shape('Anchor bolt',u.Vector(x+dx,y+dy,13),u.Vector(.065,.065,.12),'rust',mesh=cylinder,solid=False)
for x in [-2800,-2000]:
    for y in [400,-800]:
        shape('Tank service outlet',u.Vector(x+212,y,85),u.Vector(.34,.34,.7),'steel',mesh=cylinder,rotation=u.Rotator(90,0,0))
        shape('Tank pressure gauge',u.Vector(x+245,y,132),u.Vector(.18,.18,.07),'paper',mesh=cylinder,rotation=u.Rotator(90,0,0),solid=False)
for i in range(180):
    x=rng.uniform(-3400,2600);y=rng.uniform(-3000,3000)
    # Do not bridge basement stair openings with extra colliders.
    shape('Loose debris',u.Vector(x,y,1.5),u.Vector(rng.uniform(.05,.24),rng.uniform(.08,.30),.015),'paper' if i%3==0 else 'dark',rotation=u.Rotator(0,rng.uniform(0,360),0),solid=False)

start=E.spawn_actor_from_class(u.PlayerStart,cv(DATA['spawn'])+u.Vector(0,0,10),u.Rotator(0,-25,0))
start.set_actor_label('Factory insertion')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C'))
u.EditorLevelLibrary.set_level_viewport_camera_info(cv([-29,2,-24]),u.Rotator(-3,-25,0))
L.save_current_level()
u.EditorAssetLibrary.save_directory(BASE)
u.log('FACTORY_BUILD_COMPLETE actors=%d'%len(E.get_all_level_actors()))
