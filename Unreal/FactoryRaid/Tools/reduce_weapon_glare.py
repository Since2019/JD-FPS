import unreal as u
M=u.MaterialEditingLibrary
for path in ['/Game/Game/Assets/Models/Weapons/HK416/Low','/Game/Game/Assets/Models/Weapons/HK416/Sights','/Game/Game/Assets/Models/Weapons/EOTechXPS3Scope/EOTechXPS3Mat']:
 m=u.load_asset(path)
 e=M.create_material_expression(m,u.MaterialExpressionConstant);e.r=.08;M.connect_material_property(e,'',u.MaterialProperty.MP_SPECULAR)
 for n in u.ObjectIterator():
  if n.get_outer()==m and isinstance(n,u.MaterialExpressionCustom):n.set_editor_property('code',n.get_editor_property('code').replace('N.xy*.35','N.xy*.18').replace(',.58,.9)',',.72,.94)'))
 M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
