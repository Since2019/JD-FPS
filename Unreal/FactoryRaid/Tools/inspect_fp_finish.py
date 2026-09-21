import unreal as u,os,json
report={}
cls=u.load_class(None,'/Game/Variant_Shooter/Blueprints/BP_ShooterCharacter.BP_ShooterCharacter_C');p=u.get_default_object(cls)
for c in p.get_components_by_class(u.SkeletalMeshComponent):
    report[c.get_name()]=[str(c.get_material(i)) for i in range(c.get_num_materials())]
    for i in range(c.get_num_materials()):
        m=c.get_material(i);report[m.get_name()]={'parent':str(m.get_editor_property('parent')),'vectors':str(u.MaterialEditingLibrary.get_vector_parameter_names(m)),'scalars':str(u.MaterialEditingLibrary.get_scalar_parameter_names(m))}
open(os.path.join(os.path.dirname(__file__),'fp_finish.json'),'w').write(json.dumps(report,indent=2))
