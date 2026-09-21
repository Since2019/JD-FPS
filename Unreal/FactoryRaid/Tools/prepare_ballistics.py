import unreal as u, os,json
TOOLS=os.path.dirname(__file__)
def editable(path,names):
    bp=u.load_asset(path)
    for name in names:u.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
    u.BlueprintEditorLibrary.compile_blueprint(bp);u.EditorAssetLibrary.save_loaded_asset(bp)
editable('/Game/Variant_Shooter/Blueprints/Pickups/BP_ShooterWeaponBase',['Aim Variance','Firing Recoil'])
# Tune the actual native projectile component and remove the template foam dart.
bp=u.load_asset('/Game/Variant_Shooter/Blueprints/Pickups/Projectiles/BP_ShooterProjectileBase')
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem);report=[]
for handle in sub.k2_gather_subobject_data_for_blueprint(bp):
    data=u.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data,bp)
    report.append(str(obj))
    if isinstance(obj,u.ProjectileMovementComponent):
        obj.set_editor_property('initial_speed',80000.)
        obj.set_editor_property('max_speed',80000.)
        obj.set_editor_property('projectile_gravity_scale',1.)
        obj.set_editor_property('should_bounce',False)
        obj.set_editor_property('force_sub_stepping',True)
    if isinstance(obj,u.StaticMeshComponent):obj.set_editor_property('hidden_in_game',True)
    if isinstance(obj,u.SphereComponent):obj.set_editor_property('sphere_radius',.25)
u.BlueprintEditorLibrary.compile_blueprint(bp);u.EditorAssetLibrary.save_loaded_asset(bp)
for path in ['/Game/Variant_Shooter/Blueprints/Pickups/Projectiles/BP_ShooterProjectile_Bullet']:
    bp=u.load_asset(path)
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        obj=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(u.SubobjectDataBlueprintFunctionLibrary.get_data(h),bp)
        if isinstance(obj,u.StaticMeshComponent):obj.set_editor_property('hidden_in_game',True)
        if isinstance(obj,u.SphereComponent):obj.set_editor_property('sphere_radius',.25)
        if isinstance(obj,u.ProjectileMovementComponent):
            obj.set_editor_property('initial_speed',80000.)
            obj.set_editor_property('max_speed',80000.)
            obj.set_editor_property('projectile_gravity_scale',1.)
            obj.set_editor_property('should_bounce',False)
            obj.set_editor_property('force_sub_stepping',True)
    u.BlueprintEditorLibrary.compile_blueprint(bp);u.EditorAssetLibrary.save_loaded_asset(bp)
task=u.AssetExportTask();task.object=u.load_asset('/Game/Weapons/Rifle/Meshes/SM_Rifle');task.filename=os.path.join(TOOLS,'rifle_geometry.obj');task.automated=True;task.prompt=False;task.replace_identical=True
task.exporter=u.StaticMeshExporterOBJ();report.append(u.Exporter.run_asset_export_task(task))
open(os.path.join(TOOLS,'ballistics_prepare.json'),'w').write(json.dumps(report,indent=2))
asset_tools=u.AssetToolsHelpers.get_asset_tools()
for name,color,emissive in [('M_MuzzleFlash',(18,5,.6),True),('M_ImpactSpark',(8,2,.2),True),('M_ImpactMark',(.012,.010,.009),False)]:
    path='/Game/Factory/Effects/'+name
    material=u.load_asset(path)
    if not material:
        material=asset_tools.create_asset(name,'/Game/Factory/Effects',u.Material,u.MaterialFactoryNew())
        c=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant3Vector)
        c.constant=u.LinearColor(*color,1)
        u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR if emissive else u.MaterialProperty.MP_BASE_COLOR)
        if emissive:material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
        rough=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant);rough.r=.95
        u.MaterialEditingLibrary.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
        u.MaterialEditingLibrary.recompile_material(material)
    u.EditorAssetLibrary.save_loaded_asset(material)
name='M_TacticalRifle';material=u.load_asset('/Game/Factory/Effects/'+name)
if not material:
    material=asset_tools.create_asset(name,'/Game/Factory/Effects',u.Material,u.MaterialFactoryNew())
    sample=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionTextureSample)
    sample.texture=u.load_asset('/Game/Weapons/Rifle/Textures/T_Rifle_BC')
    tint=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant3Vector);tint.constant=u.LinearColor(.13,.15,.17,1)
    multiply=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionMultiply)
    u.MaterialEditingLibrary.connect_material_expressions(sample,'RGB',multiply,'A');u.MaterialEditingLibrary.connect_material_expressions(tint,'',multiply,'B')
    u.MaterialEditingLibrary.connect_material_property(multiply,'',u.MaterialProperty.MP_BASE_COLOR)
    normal=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionTextureSample)
    normal.texture=u.load_asset('/Game/Weapons/Rifle/Textures/T_Rifle_N');normal.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
    u.MaterialEditingLibrary.connect_material_property(normal,'RGB',u.MaterialProperty.MP_NORMAL)
    for value,pin in [(.48,u.MaterialProperty.MP_ROUGHNESS),(.55,u.MaterialProperty.MP_METALLIC)]:
        expr=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant);expr.r=value
        u.MaterialEditingLibrary.connect_material_property(expr,'',pin)
    u.MaterialEditingLibrary.recompile_material(material)
material.set_editor_property('used_with_skeletal_mesh',True)
u.MaterialEditingLibrary.recompile_material(material)
u.EditorAssetLibrary.save_loaded_asset(material)
