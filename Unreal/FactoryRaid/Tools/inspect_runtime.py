import unreal as u, os, json
names=[(u.SystemLibrary,'line_trace_single'),(u.SystemLibrary,'sphere_trace_single'),(u.SystemLibrary,'print_string'),(u.GameplayStatics,'begin_deferred_actor_spawn_from_class'),(u.GameplayStatics,'finish_spawning_actor'),(u.GameplayStatics,'apply_damage'),(u.PlayerController,'is_input_key_down'),(u.SceneComponent,'set_relative_location'),(u.PlayerCameraManager,'set_fov'),(u.Actor,'call_method')]
report={str(owner)+'.'+name:getattr(owner,name).__doc__ if hasattr(owner,name) else 'MISSING' for owner,name in names}
open(os.path.join(os.path.dirname(__file__),'runtime_api.json'),'w',encoding='utf-8').write(json.dumps(report,indent=2))
