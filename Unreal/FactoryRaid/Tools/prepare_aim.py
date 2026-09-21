import unreal as u
source='/Game/Variant_Shooter/Anims/ABP_FP_Weapon'
target='/Game/Factory/Animation/ABP_TacticalWeapon'
bp=u.load_asset(target)
if not bp:bp=u.EditorAssetLibrary.duplicate_asset(source,target)
assert bp
u.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'Is Aiming',True)
u.BlueprintEditorLibrary.compile_blueprint(bp)
cls=u.load_class(None,target+'.ABP_TacticalWeapon_C')
u.get_default_object(cls).set_editor_property('Is Aiming',False)
assert u.EditorAssetLibrary.save_loaded_asset(bp)
