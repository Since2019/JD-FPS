extends RigidBody3D

var shooter: CollisionObject3D
var fuse := 3.5

func _ready() -> void:
	collision_layer = 0
	collision_mask = 1
	mass = 0.4
	physics_material_override = PhysicsMaterial.new()
	physics_material_override.bounce = 0.3
	var mesh := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.06
	sphere.height = 0.12
	mesh.mesh = sphere
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("515a32")
	mesh.material_override = mat
	add_child(mesh)
	var collision := CollisionShape3D.new()
	var shape := SphereShape3D.new()
	shape.radius = 0.06
	collision.shape = shape
	add_child(collision)
	angular_velocity = Vector3(4, 6, 2)

func _physics_process(delta: float) -> void:
	fuse -= delta
	if fuse <= 0:
		set_physics_process(false)
		explode()

func explode() -> void:
	var targets := get_tree().get_nodes_in_group("combat_ai")
	var player: Node = get_tree().current_scene.get("player")
	if is_instance_valid(player): targets.append(player)
	for target in targets:
		var aim: Vector3 = target.global_position + Vector3.UP * (0.15 if target == player else 0.9)
		var distance := global_position.distance_to(aim)
		if distance > 8: continue
		var query := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP * 0.12, aim)
		query.collision_mask = 1
		if not get_world_3d().direct_space_state.intersect_ray(query).is_empty(): continue
		var amount := 210 * pow(1 - distance / 8, 1.3)
		if target.has_method("take_damage"): target.take_damage(amount, "thorax", 50)
		elif target.has_method("receive_bullet"): target.receive_bullet(amount, aim, 50)
	var light := OmniLight3D.new()
	light.position = global_position
	light.light_color = Color(1, 0.55, 0.2)
	light.light_energy = 12
	light.omni_range = 12
	get_tree().current_scene.add_child(light)
	get_tree().create_timer(0.18).timeout.connect(light.queue_free)
	if is_instance_valid(player):
		player.gunshot_heard.emit(global_position, 100)
		var audio := AudioStreamPlayer3D.new()
		audio.stream = player.gunshot_player.stream
		audio.pitch_scale = 0.45
		audio.unit_size = 20
		audio.position = global_position
		get_tree().current_scene.add_child(audio)
		audio.play()
		audio.finished.connect(audio.queue_free)
	queue_free()
