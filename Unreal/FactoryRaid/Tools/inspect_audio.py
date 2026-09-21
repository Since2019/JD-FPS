import unreal as u,os,json
out={}
settings=u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'))
for n in ['EnableGameSound','SoloAudioInFirstPIEClient','CreateAudioDeviceForEveryPlayer','bUseNonRealtimeAudioDevice']:
    try:out[n]=str(settings.get_editor_property(n))
    except Exception as e:out[n]=str(e)
for p in ['/Game/Factory/Audio/Step_Concrete','/Game/Weapons/GrenadeLauncher/Audio/FirstPersonTemplateWeaponFire02']:
    a=u.load_asset(p);out[p]={}
    for n in ['duration','volume','sound_class_object','num_channels','sample_rate','virtualization_mode']:
        try:out[p][n]=str(a.get_editor_property(n))
        except:pass
out['editor_audio_methods']=[n for n in dir(u.UnrealEditorSubsystem) if any(t in n for t in ['audio','volume','focus'])]
open(os.path.join(os.path.dirname(__file__),'audio_inspect.json'),'w').write(json.dumps(out,indent=2))
