import unreal as u,os,json
T=os.path.dirname(__file__);R={}
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Factory/Maps/ClassicFactoryTactical')
R['assets']=[str(x) for x in u.EditorAssetLibrary.list_assets('/Game') if any(s in str(x).lower() for s in ['anim','widget','hud','crosshair'])]
R['light']=[{'name':a.get_actor_label(),'type':a.get_class().get_name(),'pos':str(a.get_actor_location()),'intensity':a.light_component.intensity,'radius':a.light_component.attenuation_radius} for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,(u.PointLight,u.SpotLight))]
R['components']={c.__name__:{n:str(getattr(c,n).__doc__) for n in dir(c) if any(k in n for k in ['pause_anims','play_animation','tick_group','leader_pose','snapshot','get_all_widgets','widget_from_name'])} for c in [u.SkeletalMeshComponent]}
open(os.path.join(T,'look_inspect.json'),'w').write(json.dumps(R,indent=2))

