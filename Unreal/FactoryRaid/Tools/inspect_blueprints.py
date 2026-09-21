import unreal as u
paths=['/Game/Variant_Shooter/Blueprints/BP_ShooterGameMode','/Game/Variant_Shooter/Blueprints/BP_ShooterCharacter','/Game/Variant_Shooter/Blueprints/AI/BP_ShooterNPC']
for path in paths:
    cls=u.load_class(None,path+'.'+path.split('/')[-1]+'_C')
    if not cls:continue
    obj=u.get_default_object(cls)
    u.log('INSPECT '+path)
    for name in dir(obj):
        if any(key in name for key in ['weapon','health','life','hp','ammo','pawn','team','speed','camera','mesh']):
            try:
                val=obj.get_editor_property(name)
                u.log('PROP '+name+' = '+str(val))
            except Exception:pass
