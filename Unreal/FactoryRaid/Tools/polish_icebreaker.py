import unreal as u, math
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker')
E=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in E.get_all_level_actors():
    loc=a.get_actor_location()
    if a.get_actor_label().startswith('Pack ice '):
        a.set_actor_rotation(u.Rotator(yaw=a.get_actor_rotation().roll or a.get_actor_rotation().yaw),False)
    if a.actor_has_tag('IcebreakerEnemy'):a.set_actor_rotation(u.Rotator(yaw=180),False)
    if isinstance(a,u.TextRenderActor):a.set_actor_rotation(u.Rotator(yaw=180 if a.get_actor_location().x!=220 else 0),False)
    if a.get_actor_label() in ['Welded railing stanchion','Continuous safety rail'] and abs(loc.y+540)<1 and loc.z>360:
        E.destroy_actor(a);continue
    if isinstance(a,u.PointLight) and a.get_actor_location().z<320:
        a.light_component.set_intensity(24000)
        a.light_component.set_editor_property('attenuation_radius',1000.)
    if isinstance(a,u.StaticMeshActor) and a.get_actor_label()=='Insulated main deck bulkhead':
        loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x,loc.y,170),False,True)
        scale=a.get_actor_scale3d();a.set_actor_scale3d(u.Vector(scale.x,scale.y,3.4))
def rod(a,b,r):
    v=u.Vector(*b)-u.Vector(*a);p=(u.Vector(*a)+u.Vector(*b))*.5
    actor=E.spawn_actor_from_class(u.StaticMeshActor,p,u.MathLibrary.make_rot_from_z(v));actor.set_actor_label('Upper deck stair opening railing')
    c=actor.static_mesh_component;c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cylinder'));c.set_material(0,u.load_asset('/Game/Icebreaker/Materials/M_White'));c.set_collision_profile_name('BlockAll')
    actor.set_actor_scale3d(u.Vector(r*2/100,r*2/100,v.length()/100))
# Preserve a 2.8 m opening from the stair landing onto the upper deck.
for a in list(E.get_all_level_actors()):
    if a.get_actor_label()=='Upper deck stair opening railing':E.destroy_actor(a)
for start,end in [(-1500,-500),(-220,-170)]:
    count=max(1,int((end-start)/160))
    for i in range(count+1):
        x=start+(end-start)*i/count;rod((x,-540,360),(x,-540,465),2.5)
    for z in [415,465]:rod((start,-540,z),(end,-540,z),2.3)
assert L.save_current_level()
u.log('ICEBREAKER_POLISH_SAVED')
