"""Add a small service corner to the existing map, no map rebuild."""
import unreal as u,os,json,shutil
T=os.path.dirname(__file__);ROOT=os.path.dirname(T);E=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
path='/Game/Icebreaker/Maps/Icebreaker';source=os.path.join(ROOT,'Content','Icebreaker','Maps','Icebreaker.umap');backup=os.path.join(T,'PolyHavenBackup','Icebreaker.umap')
os.makedirs(os.path.dirname(backup),exist_ok=True)
if not os.path.exists(backup):shutil.copy2(source,backup)
L.load_level(path);assets={a['id']:a for a in json.load(open(os.path.join(T,'polyhaven_import.json')))['assets']};report=[]
for name,pos,yaw in [('portable_generator',(-1320,265,0),180),('metal_tool_chest',(-1320,410,0),180),('old_military_crate',(-1320,-350,0),90)]:
    data=assets[name];mesh=u.load_asset(data['mesh']);label='PH Service | '+name
    actor=next((a for a in E.get_all_level_actors() if a.get_actor_label()==label),None) or E.spawn_actor_from_class(u.StaticMeshActor,u.Vector())
    actor.set_actor_label(label);actor.set_folder_path('Realism/PolyHaven Service');actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(u.Vector(1,1,1));actor.set_actor_rotation(u.Rotator(yaw=yaw),False)
    actor.set_actor_location(u.Vector(pos[0],pos[1],pos[2]-data['origin_cm'][2]+data['dimensions_cm'][2]/2),False,True)
    actor.static_mesh_component.set_collision_profile_name('BlockAll');actor.set_actor_enable_collision(True)
    report.append({'id':name,'position':pos,'yaw':yaw,'scale':1,'label':label})
assert L.save_current_level();open(os.path.join(T,'polyhaven_placement.json'),'w').write(json.dumps(report,indent=2))
