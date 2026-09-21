import unreal as u,os,json
report={}
for path in ['/Game/IMC_Default','/Game/Input/IMC_Default','/Game/Input/IMC_Weapons','/Game/Variant_Shooter/Input/IMC_Weapons','/Game/Factory/Visual3/Input/IMC_TacticalWeapons']:
    ctx=u.load_asset(path)
    if not ctx:continue
    rows=[]
    for m in ctx.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        mods=[]
        for x in m.modifiers:
            data={'class':x.get_class().get_name()}
            for field in ['order','x','y','z']:
                try:data[field]=str(x.get_editor_property(field))
                except Exception:pass
            mods.append(data)
        rows.append({'key':str(m.key.get_editor_property('key_name')),'action':str(m.action),'modifiers':mods})
    report[path]=rows
report['api']={n:str(getattr(u.EnhancedInputLocalPlayerSubsystem,n).__doc__) for n in dir(u.EnhancedInputLocalPlayerSubsystem) if 'mapping' in n}
p=u.get_default_object(u.load_class(None,'/Game/Variant_Shooter/Blueprints/BP_ShooterCharacter.BP_ShooterCharacter_C'))
report['pawn']={'yaw':p.get_editor_property('use_controller_rotation_yaw'),'orient':p.character_movement.get_editor_property('orient_rotation_to_movement')}
open(os.path.join(os.path.dirname(__file__),'movement_inspect.json'),'w').write(json.dumps(report,indent=2))
