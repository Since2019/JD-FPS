extends SceneTree

var output: Dictionary = {"meshes": [], "lights": [], "doors": [], "loot": [], "exits": []}
func vec(v: Vector3) -> Array:
	return [v.x, v.y, v.z]
func _initialize() -> void:
	call_deferred("export_map")
func export_map() -> void:
	var factory = load("res://scripts/classic_factory.gd").new()
	root.add_child(factory)
	for door in factory.doors:
		output.doors.append({"position": vec(door.global_position), "rotation": vec(door.global_rotation_degrees), "locked": door.locked, "title": door.title})
	for entry in factory.loot:
		output.loot.append({"position": vec(entry.position), "title": entry.title, "item": entry.item})
	for entry in factory.exits:
		output.exits.append({"position": vec(entry.position), "title": entry.name, "key": entry.key, "radius": entry.radius})
	output.spawn = vec(factory.spawn_position)
	output.enemies = []
	for pos in factory.enemy_spawns: output.enemies.append(vec(pos))
	walk(factory, factory)
	var file = FileAccess.open("res://Unreal/FactoryRaid/Tools/factory_layout.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(output, "\t"))
	print("UE_EXPORT meshes=", output.meshes.size(), " lights=", output.lights.size())
	quit()
func walk(node: Node, factory: Node) -> void:
	if node is Node3D and node in factory.doors: return
	if node is MeshInstance3D and (node.mesh is BoxMesh or node.mesh is CylinderMesh):
		var mat = node.material_override
		var key = "steel"
		for k in factory.materials:
			if factory.materials[k] == mat: key = k
		var size = node.mesh.size if node.mesh is BoxMesh else Vector3(node.mesh.top_radius * 2, node.mesh.height, node.mesh.top_radius * 2)
		output.meshes.append({"name": str(node.get_parent().name), "shape": "box" if node.mesh is BoxMesh else "cylinder", "position": vec(node.global_position), "basis_x": vec(node.global_basis.x), "basis_y": vec(node.global_basis.y), "rotation": vec(node.global_rotation_degrees), "size": vec(size), "material": key, "solid": node.get_parent() is StaticBody3D, "emission": mat != null and mat.emission_enabled})
	if node is OmniLight3D or node is SpotLight3D:
		output.lights.append({"position": vec(node.global_position), "color": [node.light_color.r, node.light_color.g, node.light_color.b], "energy": node.light_energy, "range": node.omni_range if node is OmniLight3D else node.spot_range, "spot": node is SpotLight3D})
	for child in node.get_children(): walk(child, factory)
