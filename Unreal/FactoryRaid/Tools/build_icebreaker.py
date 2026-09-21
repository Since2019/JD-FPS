"""Build a separate playable Icebreaker environment. Existing factory assets are untouched."""
import unreal as u, os, math, random, json
T=os.path.dirname(__file__);B='/Game/Icebreaker';MAP=B+'/Maps/Icebreaker'
A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
E=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
tasks=[]
for file in os.listdir(os.path.join(T,'IcebreakerSource')):
    if not file.endswith(('.jpg','.obj')):continue
    task=u.AssetImportTask();task.filename=os.path.join(T,'IcebreakerSource',file);task.destination_path=B+('/Meshes' if file.endswith('.obj') else '/Textures');task.destination_name=os.path.splitext(file)[0];task.automated=True;task.save=True;task.replace_existing=True
    if file.endswith('.obj'):
        opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False
        opts.static_mesh_import_data.set_editor_property('combine_meshes',True);opts.static_mesh_import_data.set_editor_property('auto_generate_collision',False);task.options=opts
    tasks.append(task)
A.import_asset_tasks(tasks)
def expr(m,cls):return M.create_material_expression(m,cls)
def const(m,val,prop):
    e=expr(m,u.MaterialExpressionConstant3Vector if isinstance(val,tuple) else u.MaterialExpressionConstant)
    if isinstance(val,tuple):e.constant=u.LinearColor(*val,1)
    else:e.r=val
    M.connect_material_property(e,'',prop);return e
def custom(m,code,nodes,prop,scalar=False):
    e=expr(m,u.MaterialExpressionCustom);e.set_editor_property('code',code);e.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else u.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs=[]
    for key in nodes:
        i=u.CustomInput();i.set_editor_property('input_name',key);inputs.append(i)
    e.set_editor_property('inputs',inputs)
    for key,node in nodes.items():M.connect_material_expressions(node,'',e,key)
    M.connect_material_property(e,'',prop)
def material(name,color,rough=.55,metal=0,glow=False):
    m=u.load_asset(B+'/Materials/'+name) or A.create_asset(name,B+'/Materials',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
    c=const(m,color,u.MaterialProperty.MP_BASE_COLOR);const(m,rough,u.MaterialProperty.MP_ROUGHNESS);const(m,metal,u.MaterialProperty.MP_METALLIC)
    if glow:const(m,color,u.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        p=expr(m,u.MaterialExpressionWorldPosition)
        custom(m,'float n=frac(sin(dot(floor(P*1.5),float3(12.9898,78.233,37.719)))*43758.5453);return C*(.97+.03*n);',{'P':p,'C':c},u.MaterialProperty.MP_BASE_COLOR)
    M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);return m
mat={k:material('M_'+k,c,r,mt) for k,c,r,mt in [
 ('Hull',(.30,.055,.018),.6,0),('White',(.52,.58,.57),.52,0),('Dark',(.022,.032,.037),.52,.55),('Steel',(.25,.29,.30),.32,.85),('Yellow',(.68,.35,.035),.57,0),('Blue',(.065,.14,.17),.65,0),('Rubber',(.014,.018,.02),.87,0),('Snow',(.70,.79,.83),.82,0),('Ice',(.28,.47,.55),.28,0),('Water',(.012,.035,.045),.16,.15),('Green',(.045,.18,.13),.62,0)]}
mat['Lamp']=material('M_Lamp',(6.,5.5,4.3),glow=True)
mat['Screen']=material('M_Screen',(.02,.28,.23),glow=True)
m=material('M_Deck',(.2,.23,.21));m.set_editor_property('tangent_space_normal',False)
p=expr(m,u.MaterialExpressionWorldPosition);n=expr(m,u.MaterialExpressionVertexNormalWS)
for ch,prop in [('diff',u.MaterialProperty.MP_BASE_COLOR),('rough',u.MaterialProperty.MP_ROUGHNESS),('nor_dx',u.MaterialProperty.MP_NORMAL)]:
    tex=u.load_asset(B+'/Textures/metal_plate_'+ch+'_2k');assert tex
    tex.set_editor_property('srgb',ch=='diff');tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT);u.EditorAssetLibrary.save_loaded_asset(tex)
    obj=expr(m,u.MaterialExpressionTextureObject);obj.texture=tex
    prefix='float3 w=pow(abs(N),8);w/=max(dot(w,1),.001);float3 p=P/50.;'
    if ch=='nor_dx':code=prefix+'float3 a=Texture2DSample(Tex,TexSampler,p.yz).rgb*2-1;float3 b=Texture2DSample(Tex,TexSampler,p.xz).rgb*2-1;float3 c=Texture2DSample(Tex,TexSampler,p.xy).rgb*2-1;return normalize(float3(sign(N.x)*a.z,a.x*.5,a.y*.5)*w.x+float3(b.x*.5,sign(N.y)*b.z,b.y*.5)*w.y+float3(c.x*.5,c.y*.5,sign(N.z)*c.z)*w.z);'
    else:code=prefix+'float3 c=Texture2DSample(Tex,TexSampler,p.yz).rgb*w.x+Texture2DSample(Tex,TexSampler,p.xz).rgb*w.y+Texture2DSample(Tex,TexSampler,p.xy).rgb*w.z;'+('return c*.85;' if ch=='diff' else 'return clamp(c.r,.4,.94);')
    custom(m,code,{'Tex':obj,'P':p,'N':n},prop,ch=='rough')
M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);mat['Deck']=m
if u.EditorAssetLibrary.does_asset_exist(MAP):
    L.load_level(MAP)
    for actor in E.get_all_level_actors():
        if not isinstance(actor,(u.WorldSettings,u.LevelScriptActor)):E.destroy_actor(actor)
else:L.new_level(MAP)
cube=u.load_asset('/Engine/BasicShapes/Cube');cyl=u.load_asset('/Engine/BasicShapes/Cylinder')
def shape(label,pos,size,material='White',mesh=None,rot=None,solid=True):
    a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),rot or u.Rotator());a.set_actor_label(label)
    c=a.static_mesh_component;c.set_static_mesh(mesh or cube);c.set_material(0,mat[material]);c.set_collision_profile_name('BlockAll' if solid else 'NoCollision')
    a.set_actor_scale3d(u.Vector(*(v/100 for v in size)));return a
def rod(label,a,b,r=3,material='Steel',solid=False):
    v=u.Vector(*b)-u.Vector(*a);pos=(u.Vector(*a)+u.Vector(*b))*.5
    return shape(label,(pos.x,pos.y,pos.z),(r*2,r*2,v.length()),material,cyl,u.MathLibrary.make_rot_from_z(v),solid)
def text(label,pos,yaw=180,size=22):
    a=E.spawn_actor_from_class(u.TextRenderActor,u.Vector(*pos),u.Rotator(yaw=yaw));a.set_actor_label('Sign | '+label)
    c=a.text_render;c.set_text(label);c.set_world_size(size);c.set_text_render_color(u.Color(205,215,203,255));return a
def light(pos,power=4500,color=(1,.86,.69),radius=850):
    a=E.spawn_actor_from_class(u.PointLight,u.Vector(*pos));c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(power);c.set_light_color(u.LinearColor(*color,1));c.set_editor_property('attenuation_radius',radius);c.set_editor_property('source_radius',12.)
    return a
def rail(a,b,z=0):
    distance=math.dist(a,b);count=max(1,int(distance/160))
    for i in range(count+1):
        x=a[0]+(b[0]-a[0])*i/count;y=a[1]+(b[1]-a[1])*i/count
        rod('Welded railing stanchion',(x,y,z),(x,y,z+105),2.5,'White',True)
    for h in [55,105]:rod('Continuous safety rail',(*a,z+h),(*b,z+h),2.3,'White',True)
def box(label,x,y,z,w,d,h,material='Blue'):
    shape(label,(x,y,z+h/2),(w,d,h),material)
    for yy in [y-d/2-1,y+d/2+1]:
        for zz in [z+8,z+h-8]:shape(label+' welded rim',(x,yy,zz),(w,3,4),'Steel',solid=False)
        for xx in [x-w/2+12,x+w/2-12]:shape(label+' corner guard',(xx,yy,z+h/2),(5,3,h),'Dark',solid=False)
def loot(i,pos,title,item):
    x,y,z=pos;box('Search case '+title,x,y,z,100,62,65,'Green')
    a=E.spawn_actor_from_class(u.TargetPoint,u.Vector(x,y,z+80));a.set_actor_label('Loot | '+title);a.set_editor_property('tags',['Loot',str(i),item])
# The hull is a continuous authored surface. The deck uses triangle collision,
# avoiding a convex hull that would seal interiors or expose invisible floors at the bow.
for name,key,collision in [('SM_IcebreakerHull','Hull',False),('SM_Deck','Deck',True)]:
    mesh=u.load_asset(B+'/Meshes/'+name);assert mesh
    if collision:
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);u.EditorAssetLibrary.save_loaded_asset(mesh)
    shape(name,(0,0,0),(100,100,100),key,mesh,solid=collision)
# Sea and ice fields stay below the gunplay area; railings bound the walkable deck.
shape('Arctic ocean',(0,0,-480),(150000,150000,30),'Water',solid=False)
rng=random.Random(805)
ice=u.load_asset(B+'/Meshes/SM_IceFloe')
for i in range(175):
    x=rng.uniform(-22000,24000);y=rng.uniform(-18000,18000)
    if abs(x)<4600 and abs(y)<1200:continue
    s=rng.uniform(1.4,11)
    shape('Pack ice %03d'%i,(x,y,-452+rng.uniform(-9,9)),(s*100,s*rng.uniform(.65,1.3)*100,100),'Snow',ice,u.Rotator(yaw=rng.uniform(0,360)),False)
outline=[(-3900,700),(-3200,850),(-1200,870),(1200,830),(2300,740),(3000,590),(3500,380),(3850,120)]
for side in [-1,1]:
    pts=[(x,y*side) for x,y in outline]
    for a,b in zip(pts,pts[1:]):rail(a,b)
rail((-3900,-700),(-3900,700));rail((3850,-120),(3850,120))
# Main deck superstructure: machinery aft, accommodation forward. Two open
# bulkhead doors connect the internal route; clear side decks remain on both sides.
for y in [-560,560]:
    shape('Insulated main deck bulkhead',(100,y,170),(3200,16,340),'White')
    shape('Protective lower paint',(100,y-10 if y<0 else y+10,42),(3200,3,84),'Green',solid=False)
for x in [-1500,200,1700]:
    for y in [-337,337]:shape('Watertight bulkhead',(x,y,160),(18,446,320),'White')
    shape('Door lintel',(x,0,285),(24,228,70),'White')
    for y in [-113,113]:shape('Door frame',(x,y,125),(28,7,250),'Steel')
    text('ENGINE ROOM' if x==-1500 else 'CREW / BRIDGE',(x-12,-95,238),180,16)
shape('Upper deck floor',(100,0,350),(3200,1140,20),'Deck')
# Low foredeck roof extension; fully clear headroom throughout the main level.
for x in [-1250,-750,-250,350,950,1450]:
    shape('Ceiling rib',(x,0,314),(9,1110,12),'White',solid=False)
    shape('Protected luminaire',(x,0,301),(68,20,8),'Dark',solid=False)
    shape('Diffuser',(x,0,296),(58,16,2),'Lamp',solid=False);light((x,0,270),24000,radius=1000)
    for y in [-520,520]:rod('Overhead service pipe',(x-250,y,278),(x+250,y,278),4,'Steel')
# Exterior stair has 18 cm risers and 32 cm treads, plus a full landing.
for i in range(20):
    x=-1100+i*32;h=(i+1)*18
    shape('Stair tread %02d'%i,(x,-690,h-3),(34,176,6),'Deck')
    shape('Stair riser',(x+16,-690,h-9),(3,176,18),'White')
for y in [-782,-598]:
    rod('Stair stringer',(-1118,y,0),(-478,y,360),6,'Dark',True)
    rod('Stair handrail',(-1118,y,95),(-478,y,455),2.5,'White',True)
shape('Stair landing',(-360,-665,350),(272,230,20),'Deck')
# Bridge level: a central entry, clear glazing apertures and instrument panels.
for y in [-470,470]:
    shape('Bridge lower side',(700,y,418),(1700,15,116),'White')
    shape('Bridge upper side',(700,y,639),(1700,15,46),'White')
    for x in [-150,200,550,900,1250,1550]:shape('Window mullion',(x,y,551),(8,18,150),'Dark')
for x in [-150,1550]:
    for y in [-320,320]:shape('Bridge end bulkhead',(x,y,470),(18,300,220),'White')
    shape('Bridge door head',(x,0,630),(18,350,62),'White')
shape('Bridge roof',(700,0,672),(1770,1030,20),'White')
shape('Bridge console',(1270,0,407),(110,690,94),'Dark')
for y in [-240,-80,80,240]:
    shape('Instrument bezel',(1209,y,463),(7,119,68),'Rubber',rot=u.Rotator(0,0,0))
    shape('Navigation display',(1204,y,463),(2,102,52),'Screen',solid=False)
    for z in [453,463,473]:shape('Screen plotting line',(1202,y,z),(1,86,1),'Green',solid=False)
light((500,0,620),5500,(.77,.86,1),1100)
text('ICEBREAKER  /  BRIDGE',(-161,-150,593),180,18)
rail((-1500,540),(-170,540),360)
rail((-1500,-540),(-500,-540),360)
rail((-220,-540),(-170,-540),360)
rail((-1500,-540),(-1500,540),360)
# Exhaust trunk, equipment deck and radio mast.
box('Exhaust trunk',-920,120,360,310,350,540,'White')
box('Funnel cap',-920,120,870,340,380,60,'Dark')
for y in [20,120,220]:rod('Exhaust outlet',(-920,y,920),(-920,y,1000),32,'Dark')
rod('Communications mast',(650,0,682),(650,0,1370),11,'White')
rod('Radar cross arm',(650,-250,1130),(650,250,1130),5,'White')
shape('Radar array',(650,0,1260),(30,330,27),'White',solid=False)
for y in [-220,220]:rod('Antenna',(650,y,1125),(650,y,1460),1.5,'Dark')
# Machinery is assembled with clearly separated service aisle and repeated
# engine cylinders, heat shields and pipework, rather than giant blocking cubes.
for y in [-335,335]:
    box('Diesel generator skid',-650,y,8,840,270,45,'Dark')
    box('Generator crankcase',-650,y,53,650,205,105,'Green')
    for x in [-910,-800,-690,-580,-470,-360]:
        shape('Cylinder head',(x,y,180),(90,175,54),'Steel')
        rod('Injection pipe',(x,y-60,211),(x,y+60,211),2,'Dark')
    rod('Generator alternator',(-1120,y,126),(-970,y,126),78,'Blue',True)
    rod('Exhaust manifold',(-970,y,241),(-300,y,241),12,'Dark')
for x in [460,840,1240]:
    box('Crew locker',x,475,0,90,125,215,'Blue')
    shape('Locker handle',(x,409,110),(8,5,25),'Steel',solid=False)
    for z in [165,173,181]:shape('Locker louvre',(x,411,z),(58,3,2),'Dark',solid=False)
box('Chart table',1060,-310,0,250,135,80,'White')
text('02  /  CREW',(220,-290,245),0,26)
# Cargo work deck with corrugated containers, lashings, bollards and deck crane.
for idx,(x,y) in enumerate([(-2900,190),(-2150,220),(2300,-160)]):
    box('Cargo container',x,y,0,605,244,259,'Blue' if idx!=1 else 'Hull')
    for side in [-1,1]:
        for xx in range(-275,280,25):shape('Container corrugation',(x+xx,y+side*124,132),(8,5,229),'Blue' if idx!=1 else 'Hull',solid=False)
    for yy in [-65,65]:rod('Container door locking bar',(x-306,y+yy,12),(x-306,y+yy,243),2,'Steel')
    text('ARCTIC  /  '+str(410+idx),(x-309,y-90,170),180,20)
for x in [-3550,-1700,3200]:
    for y in [-640,640]:
        shape('Bollard base',(x,y,8),(110,75,16),'Dark')
        for dx in [-30,30]:rod('Mooring bollard',(x+dx,y,15),(x+dx,y,65),12,'Dark',True)
shape('Crane pedestal',(-2100,-410,95),(155,155,190),'Yellow',cyl)
rod('Deck crane boom',(-2100,-410,160),(-2650,-310,630),24,'Yellow',True)
rod('Crane cable',(-2650,-310,630),(-2650,-310,230),1,'Dark')
for side in [-1,1]:
    for x in [-3300,-2000,2000,2900]:
        shape('Deck snow drift',(x,side*770,3),(320,80,6),'Snow',solid=False)
for i,(p,title,item) in enumerate([
 ((-3520,-210,0),'船尾工具箱','工具'),((-2200,-635,0),'甲板补给','弹药'),((-1250,280,0),'机舱维修箱','工具'),((950,-280,84),'船员医疗箱','医疗包'),((370,315,360),'船桥文件箱','情报'),((3150,110,0),'船首急救箱','医疗包')]):loot(i,p,title,item)
for i,pos in enumerate([(-2400,-430,98),(-800,0,98),(950,0,98),(400,130,458),(2150,540,98),(3050,-430,98)]):
    a=E.spawn_actor_from_class(u.load_class(None,'/Game/Variant_Shooter/Blueprints/AI/BP_ShooterNPC.BP_ShooterNPC_C'),u.Vector(*pos),u.Rotator(yaw=180));a.set_actor_label('Icebreaker PMC %02d'%i);a.set_editor_property('tags',['FactoryEnemy','IcebreakerEnemy']);a.set_editor_property('Weapon Class',u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/Weapons/BP_ShooterWeapon_Rifle.BP_ShooterWeapon_Rifle_C'));a.character_movement.set_editor_property('max_walk_speed',170);a.character_movement.set_editor_property('run_physics_with_no_controller',True)
E.spawn_actor_from_class(u.PlayerStart,u.Vector(-3550,-520,98),u.Rotator(0,0,0))
# Overcast blue daylight with warm functional cabin lighting, no crushed blacks.
E.spawn_actor_from_class(u.SkyAtmosphere,u.Vector())
sun=E.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,2000),u.Rotator(pitch=-25,yaw=-55));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_intensity(6500);sun.light_component.set_light_color(u.LinearColor(.76,.85,1,1));sun.light_component.set_editor_property('atmosphere_sun_light',True);sun.light_component.set_editor_property('light_source_angle',8.)
sky=E.spawn_actor_from_class(u.SkyLight,u.Vector());sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('real_time_capture',True);sky.light_component.set_intensity(.8)
fog=E.spawn_actor_from_class(u.ExponentialHeightFog,u.Vector(0,0,-600));fog.component.set_editor_property('fog_density',.012);fog.component.set_editor_property('enable_volumetric_fog',True)
pp=E.spawn_actor_from_class(u.PostProcessVolume,u.Vector());pp.set_editor_property('unbound',True);s=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_HISTOGRAM),('override_auto_exposure_min_brightness',True),('auto_exposure_min_brightness',3.),('override_auto_exposure_max_brightness',True),('auto_exposure_max_brightness',11.),('override_auto_exposure_bias',True),('auto_exposure_bias',.3),('override_motion_blur_amount',True),('motion_blur_amount',0.),('override_bloom_intensity',True),('bloom_intensity',.12)]:s.set_editor_property(k,v)
pp.set_editor_property('settings',s)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Game/Variant_Shooter/Blueprints/BP_ShooterGameMode.BP_ShooterGameMode_C'))
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(-4600,-3800,2500),u.Rotator(pitch=-23,yaw=38))
assert L.save_current_level();u.EditorAssetLibrary.save_directory(B)
report={'map':MAP,'actors':len(E.get_all_level_actors()),'enemies':6,'containers':6,'complete':True,'quality':'Authored environment with scanned deck material; existing prototype character and weapon assets retained pending complete replacements.'}
open(os.path.join(T,'icebreaker_build.json'),'w').write(json.dumps(report,indent=2));u.log('ICEBREAKER_BUILD_COMPLETE')
