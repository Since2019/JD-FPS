import unreal as u,os,json
M=u.MaterialEditingLibrary;A=u.AssetToolsHelpers.get_asset_tools();P='/Game/Factory/HK416'
m=u.load_asset(P+'/M_Holographic') or A.create_asset('M_Holographic',P,u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(m);m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);m.set_editor_property('two_sided',True)
nodes={}
for name,vec in [('Forward',(0,1,0)),('Right',(1,0,0)),('Up',(0,0,1))]:
    e=M.create_material_expression(m,u.MaterialExpressionVectorParameter);e.set_editor_property('parameter_name',name);e.set_editor_property('default_value',u.LinearColor(*vec,0));nodes[name]=e
nodes['P']=M.create_material_expression(m,u.MaterialExpressionWorldPosition);nodes['Eye']=M.create_material_expression(m,u.MaterialExpressionCameraPositionWS)
e=M.create_material_expression(m,u.MaterialExpressionCustom);e.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1)
inputs=[]
for name in nodes:
    i=u.CustomInput();i.set_editor_property('input_name',name);inputs.append(i)
e.set_editor_property('inputs',inputs)
e.set_editor_property('code','float3 d=normalize(P-Eye); float facing=dot(d,Forward); float2 q=float2(dot(d,Right),dot(d,Up))/max(facing,.001); float r=length(q); float aa=max(fwidth(r),.00012); float ring=1-smoothstep(.00027,.00027+aa,abs(r-.00989)); float dotMask=1-smoothstep(.000145,.000145+aa,r); return max(ring,dotMask)*step(.5,facing);')
for name,node in nodes.items():M.connect_material_expressions(node,'',e,name)
M.connect_material_property(e,'',u.MaterialProperty.MP_OPACITY)
color=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(3,.018,.005,1);M.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
for folder in ['HK416','EOTechXPS3Scope']:
    for path in u.EditorAssetLibrary.list_assets('/Game/Game/Assets/Models/Weapons/'+folder):
        asset=u.load_asset(path)
        if isinstance(asset,u.Material):M.recompile_material(asset)
        u.EditorAssetLibrary.save_loaded_asset(asset)
open(os.path.join(os.path.dirname(__file__),'holographic_prepare.json'),'w').write(json.dumps({'ready':True}))
