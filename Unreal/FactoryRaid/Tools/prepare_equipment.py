import unreal as u
p='/Game/Variant_Shooter/Blueprints/Pickups/BP_ShooterWeaponBase'
b=u.load_asset(p)
u.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(b,'Current Bullets',True)
u.BlueprintEditorLibrary.compile_blueprint(b)
assert u.EditorAssetLibrary.save_loaded_asset(b)
u.log('EQUIPMENT_AMMO_READY')
