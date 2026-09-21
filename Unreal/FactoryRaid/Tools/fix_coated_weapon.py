import unreal as u
M=u.MaterialEditingLibrary
for path in ['/Game/Game/Assets/Models/Weapons/HK416/Low','/Game/Game/Assets/Models/Weapons/HK416/Sights','/Game/Game/Assets/Models/Weapons/EOTechXPS3Scope/EOTechXPS3Mat']:
    m=u.load_asset(path);e=M.create_material_expression(m,u.MaterialExpressionConstant);e.r=0.;M.connect_material_property(e,'',u.MaterialProperty.MP_METALLIC);M.recompile_material(m);assert u.EditorAssetLibrary.save_loaded_asset(m)
