"""Render inventory portraits from the actual in-game weapon and helmet meshes."""
import unreal as u,os,time,traceback
T=os.path.dirname(__file__);D=os.path.join(T,'Visual4Source');P='/Game/Factory/Visual4'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
if u.EditorAssetLibrary.does_asset_exist(P+'/IconStage'):L.load_level(P+'/IconStage')
else:L.new_level(P+'/IconStage')
for a in E.get_all_level_actors():
    if not isinstance(a,(u.WorldSettings,u.LevelScriptActor)):E.destroy_actor(a)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for pos,power in [((60,-80,100),1200),((-60,30,100),700)]:
    a=E.spawn_actor_from_class(u.PointLight,u.Vector(*pos));c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(power);c.set_editor_property('attenuation_radius',350.)
cap=E.spawn_actor_from_class(u.SceneCapture2D,u.Vector(100,0,40));c=cap.get_component_by_class(u.SceneCaptureComponent2D)
c.capture_every_frame=False;c.capture_on_movement=False;c.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC;c.ortho_width=105.;c.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR
rt=u.RenderingLibrary.create_render_target2d(world,256,160,u.TextureRenderTargetFormat.RTF_RGBA8);c.texture_target=rt
s=c.post_process_settings
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',4.5)]:s.set_editor_property(k,v)
c.post_process_settings=s
actors=[];phase=0;elapsed=0.;started=time.monotonic()
groups=[('Weapon',[('MK18_'+n,'M_'+m) for n,m in [('Receiver','Receiver'),('RIS','RIS'),('Hardware','Hardware'),('Polymer','Polymer'),('Dark','Dark')]],(0,10,5),(110,12,42),105),('Helmet',[('FAST_'+n,'M_'+m) for n,m in [('Shell','PMC_Helmet'),('Hardware','FAST_Hardware'),('Loop','FAST_Loop'),('Straps','FAST_Straps')]],(0,0,0),(65,-80,30),48)]
u.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
    global phase,elapsed,actors
    try:
        elapsed+=min(dt,.1)
        if phase>=len(groups):
            u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.log('LOOT_ICONS_RENDERED');return
        name,parts,center,eye,width=groups[phase]
        if not actors:
            for mesh,mat in parts:
                a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector());a.static_mesh_component.set_static_mesh(u.load_asset((P+'/Meshes/' if mesh.startswith('FAST') else '/Game/Factory/Visual3/Meshes/')+mesh))
                u.log('ICON_MATERIAL_SLOTS '+mesh+' '+str(a.static_mesh_component.get_num_materials()))
                for slot in range(max(1,a.static_mesh_component.get_num_materials())):a.static_mesh_component.set_material(slot,u.load_asset(P+'/Materials/'+mat))
                actors.append(a)
            cap.set_actor_location(u.Vector(*eye),False,True);cap.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*eye),u.Vector(*center)),False);c.ortho_width=width;elapsed=0
        if elapsed>3:
            c.capture_scene();u.RenderingLibrary.export_render_target(world,rt,D,'Icon_'+name+'.png')
            for a in actors:E.destroy_actor(a)
            actors=[];phase+=1;elapsed=0
        if time.monotonic()-started>90:raise RuntimeError('Icon render timeout')
    except Exception:u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
handle=u.register_slate_post_tick_callback(tick)
