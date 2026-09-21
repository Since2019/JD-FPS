import unreal as u,os,time,traceback
T=os.path.dirname(__file__);P='/Game/Game/Assets/Models/Weapons/'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
L.load_level('/Game/Factory/Visual4/IconStage')
for a in E.get_all_level_actors():
    if not isinstance(a,(u.WorldSettings,u.LevelScriptActor)):E.destroy_actor(a)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for pos,power in [((20,-60,80),180),((-30,40,65),120)]:
    a=E.spawn_actor_from_class(u.PointLight,u.Vector(*pos));c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(power);c.set_editor_property('attenuation_radius',400.)
for suffix in ['', '_bolt_a','_bolt_b','_scope','_trigger','_wrap']:
    a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector());a.static_mesh_component.set_static_mesh(u.load_asset('/Game/Realism/WeaponTerrain/bolt_action_rifle_7_62/bolt_action_rifle_7_62'+suffix))
cap=E.spawn_actor_from_class(u.SceneCapture2D,u.Vector(0,-150,35));c=cap.get_component_by_class(u.SceneCaptureComponent2D);c.capture_every_frame=False;c.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC;c.ortho_width=145.;c.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR
cap.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(0,-150,35),u.Vector(0,0,0)),False)
rt=u.RenderingLibrary.create_render_target2d(world,1200,700,u.TextureRenderTargetFormat.RTF_RGBA8);c.texture_target=rt
s=c.post_process_settings
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',0.)]:s.set_editor_property(k,v)
c.post_process_settings=s
u.EditorPythonScripting.set_keep_python_script_alive(True);elapsed=0
def tick(dt):
    global elapsed
    elapsed+=min(dt,.1)
    if elapsed<8:return
    c.capture_scene();u.RenderingLibrary.export_render_target(world,rt,T,'bolt762_asset_preview.png')
    task=u.AssetImportTask();task.filename=os.path.join(T,'bolt762_asset_preview.png');task.destination_path='/Game/Factory/Visual4/UI';task.destination_name='Photo_Bolt762';task.automated=True;task.replace_existing=True;task.save=True;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
handle=u.register_slate_post_tick_callback(tick)


