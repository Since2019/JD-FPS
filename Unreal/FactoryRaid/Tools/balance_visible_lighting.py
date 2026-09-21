import unreal as u,os,json
E=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Icebreaker/Maps/Icebreaker');A=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
for a in E.get_all_level_actors():
 if a.actor_has_tag('VisibleUpgradeWorklight'):E.destroy_actor(a);continue
 if isinstance(a,u.PostProcessVolume):
  s=a.get_editor_property('settings');s.set_editor_property('auto_exposure_min_brightness',3.);s.set_editor_property('auto_exposure_bias',0.);a.set_editor_property('settings',s)
 if isinstance(a,u.DirectionalLight):a.light_component.set_intensity(2500.)
m=u.load_asset('/Game/Realism/Revision2/M_Worklight') or A.create_asset('M_Worklight','/Game/Realism/Revision2',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(m)
e=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);e.constant=u.LinearColor(4,3.8,3.2,1);M.connect_material_property(e,'',u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
for x in [-1320,-250,800]:
 for y in [-380,380]:
  a=E.spawn_actor_from_class(u.PointLight,u.Vector(x,y,285));a.tags=[u.Name('VisibleUpgradeWorklight')];a.set_actor_label('Cabin service strip light');a.set_folder_path('Realism/WorkingLights');c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(3500.);c.set_editor_property('attenuation_radius',650.);c.set_editor_property('source_radius',18.);c.set_light_color(u.LinearColor(1,.96,.86,1))
  a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,320));a.tags=[u.Name('VisibleUpgradeWorklight')];a.set_actor_label('Cabin strip light diffuser');a.set_folder_path('Realism/WorkingLights');c=a.static_mesh_component;c.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));c.set_material(0,m);c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False);a.set_actor_scale3d(u.Vector(.6,.08,.04))
assert L.save_current_level()
