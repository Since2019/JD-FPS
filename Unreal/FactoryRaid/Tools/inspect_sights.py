import unreal as u, os, sys, json, traceback
TOOLS=os.path.dirname(__file__);sys.path.insert(0,TOOLS)
from tactical_runtime import TacticalSession,prop
u.EditorPythonScripting.set_keep_python_script_alive(True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level('/Game/Factory/Maps/ClassicFactoryTactical')
elapsed=0;requested=False;session=None
def inspect(obj):
    d={'class':obj.get_class().get_name(),'path':obj.get_path_name()}
    for n in ['Aim Point','Aim Target','IronSight Adjust','Is Aiming','Aim Variance','Firing Recoil','Refire Rate','Ammo','Projectile','Damage','Impulse','Damage Owner','bStartLogicAutomatically']:
        d[n]=str(prop(obj,n,'MISSING'))
    for name in dir(obj):
        if any(s in name.lower() for s in ['aim','weapon','mesh','projectile','fire','damage','speed','spread','ammo','socket','target']):
            try:d[name]=str(obj.get_editor_property(name))
            except:pass
    if isinstance(obj,u.SceneComponent):
        d.update(location=str(obj.get_world_location()),rotation=str(obj.get_world_rotation()),parent=str(obj.get_attach_parent()),socket=str(obj.get_attach_socket_name()))
    if isinstance(obj,u.MeshComponent):
        d['sockets']={str(n):str(obj.get_socket_transform(n,u.RelativeTransformSpace.RTS_WORLD)) for n in obj.get_all_socket_names()}
    return d
def tick(dt):
    global elapsed,requested,session
    try:
        if not requested:level.editor_request_begin_play();requested=True;return
        elapsed+=dt
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world or elapsed<3:return
        p=u.GameplayStatics.get_player_character(world,0)
        if not p:return
        if session is None:session=TacticalSession(world,p,True);session.ai_enabled=False
        session.update(dt,{'RightMouseButton'})
        if elapsed<5:return
        objects=[p,session.weapon,session.anim,session.camera]+list(p.get_components_by_class(u.SceneComponent))+list(session.weapon.get_components_by_class(u.SceneComponent))
        out={'objects':[inspect(o) for o in objects if o], 'rotator_doc':u.Rotator.__doc__}
        path='/Game/Variant_Shooter/Blueprints/Pickups/Projectiles/BP_ShooterProjectile_Bullet.BP_ShooterProjectile_Bullet_C'
        bullet=u.get_default_object(u.load_class(None,path));out['bullet']=inspect(bullet)
        out['bullet_components']=[inspect(o) for o in bullet.get_components_by_class(u.ActorComponent)]
        for owner,name in [(u.GameplayStatics,'spawn_emitter_at_location'),(u.AutomationLibrary,'take_high_res_screenshot')]:out[name]=getattr(owner,name).__doc__
        open(os.path.join(TOOLS,'sights_inspect.json'),'w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=2))
    except:open(os.path.join(TOOLS,'sights_inspect_error.txt'),'w').write(traceback.format_exc())
    else:
        if elapsed<5:return
    u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
handle=u.register_slate_post_tick_callback(tick)
