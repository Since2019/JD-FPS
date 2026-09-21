class_name TrainingEnemy
extends CharacterBody3D

const SOLDIER_MODEL := preload("res://assets/characters/soldier/Soldier_Male.gltf")

signal killed(enemy: TrainingEnemy)

enum AIState { PATROL, INVESTIGATE, COMBAT }

var health := 100.0
var player: FPSPlayer
var attack_timer := 0.0
var reaction_time := 0.0
var state := AIState.PATROL
var patrol_origin := Vector3.ZERO
var patrol_target := Vector3.ZERO
var last_known_position := Vector3.ZERO
var search_time := 0.0
var decision_timer := 0.0
var strafe_direction := 1.0
var active := true
var muzzle_flash: Node3D
var animation_player: AnimationPlayer
var current_animation := ""
var shot_audio: AudioStreamPlayer3D
var vitals := RaidVitals.new()
var navigator: NavigationAgent3D
var path_clock := 0.0
var footsteps: AudioStreamPlayer3D
var step_clock := 0.0

func setup(target: FPSPlayer, at: Vector3) -> void:
	player = target
	position = at
	patrol_origin = at
	patrol_target = at + Vector3(randf_range(-4.0, 4.0), 0, randf_range(-4.0, 4.0))
	player.gunshot_heard.connect(_on_gunshot_heard)

func _ready() -> void:
	add_to_group("combat_ai")
	# 主胶囊和部位 Area 都可接收子弹：射线先命中哪一个都会结算伤害。
	# 这样既保留爆头倍率，也避免胶囊遮挡部位后出现“命中但不掉血”。
	collision_layer = 4
	collision_mask = 1
	# CharacterBody3D 必须拥有实体碰撞形状，否则会直接穿过地面。
	var body_collision := CollisionShape3D.new()
	var body_capsule := CapsuleShape3D.new()
	body_capsule.radius = 0.34
	body_capsule.height = 1.85
	body_collision.shape = body_capsule
	body_collision.position = Vector3(0, 0.93, 0)
	add_child(body_collision)
	_build_body()
	shot_audio = AudioStreamPlayer3D.new()
	shot_audio.stream = player.gunshot_player.stream
	shot_audio.unit_size = 12
	shot_audio.max_distance = 65
	shot_audio.volume_db = -5
	add_child(shot_audio)
	navigator = NavigationAgent3D.new()
	navigator.path_desired_distance = 0.45
	navigator.target_desired_distance = 0.6
	add_child(navigator)
	footsteps = AudioStreamPlayer3D.new()
	footsteps.stream = player.step_audio.stream
	footsteps.unit_size = 5
	footsteps.max_distance = 25
	footsteps.volume_db = -12
	add_child(footsteps)

func _build_body() -> void:
	var soldier := SOLDIER_MODEL.instantiate()
	soldier.name = "SoldierVisual"
	soldier.scale = Vector3.ONE
	add_child(soldier)
	animation_player = soldier.find_child("AnimationPlayer", true, false) as AnimationPlayer
	add_child(_hitbox("胸部", Vector3(0.6, 0.85, 0.34), Vector3(0, 1.22, 0), 1.0, Color(0.22, 0.27, 0.18)))
	add_child(_hitbox("头部", Vector3(0.34, 0.34, 0.34), Vector3(0, 1.84, 0), 2.5, Color(0.38, 0.31, 0.25)))
	add_child(_hitbox("腿部", Vector3(0.5, 0.8, 0.28), Vector3(0, 0.42, 0), 0.65, Color(0.15, 0.18, 0.13)))
	var gear_mat := StandardMaterial3D.new()
	gear_mat.albedo_color = Color(0.07, 0.10, 0.055)
	gear_mat.roughness = 0.9
	var rifle := MeshInstance3D.new()
	var rifle_mesh := BoxMesh.new()
	rifle_mesh.size = Vector3(0.09, 0.10, 0.85)
	rifle.mesh = rifle_mesh
	rifle.position = Vector3(0.25, 1.27, -0.22)
	rifle.rotation_degrees.x = -8
	rifle.material_override = gear_mat
	add_child(rifle)
	muzzle_flash = Node3D.new()
	muzzle_flash.position = Vector3(0.25, 1.27, -0.68)
	var flash_mesh := MeshInstance3D.new()
	var flash_shape := SphereMesh.new()
	flash_shape.radius = 0.095
	flash_shape.height = 0.19
	flash_mesh.mesh = flash_shape
	var flash_mat := StandardMaterial3D.new()
	flash_mat.albedo_color = Color(1.0, 0.72, 0.22)
	flash_mat.emission_enabled = true
	flash_mat.emission = Color(1.0, 0.28, 0.015)
	flash_mat.emission_energy_multiplier = 7.0
	flash_mesh.material_override = flash_mat
	muzzle_flash.add_child(flash_mesh)
	var flash_light := OmniLight3D.new()
	flash_light.light_color = Color(1.0, 0.48, 0.12)
	flash_light.light_energy = 4.5
	flash_light.omni_range = 4.5
	muzzle_flash.add_child(flash_light)
	muzzle_flash.visible = false
	add_child(muzzle_flash)

func _hitbox(label: String, size: Vector3, pos: Vector3, multiplier: float, color: Color) -> Area3D:
	var area := Area3D.new()
	area.set_meta("part", label)
	area.set_meta("multiplier", multiplier)
	area.collision_layer = 4
	area.collision_mask = 0
	area.position = pos
	area.set_script(preload("res://scripts/hitbox.gd"))
	area.owner_enemy = self
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	area.add_child(shape)
	var mesh := MeshInstance3D.new()
	var box_mesh := BoxMesh.new()
	box_mesh.size = size
	mesh.mesh = box_mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.9
	mesh.material_override = mat
	mesh.visible = false
	area.add_child(mesh)
	return area

func _physics_process(delta: float) -> void:
	if not active or not is_instance_valid(player) or not player.raid_active: return
	if not is_on_floor(): velocity.y -= 14.0 * delta
	attack_timer -= delta
	decision_timer -= delta
	path_clock -= delta
	step_clock -= delta
	var distance := global_position.distance_to(player.global_position)
	var can_see := _can_see_player(distance)
	if can_see:
		last_known_position = player.global_position
		reaction_time += delta
		if reaction_time >= 0.7 and state != AIState.COMBAT:
			_enter_combat()
	else:
		reaction_time = maxf(reaction_time - delta * 0.6, 0.0)
	match state:
		AIState.PATROL: _patrol(delta)
		AIState.INVESTIGATE: _investigate(delta, can_see)
		AIState.COMBAT: _combat(delta, distance, can_see)
	move_and_slide()
	if Vector2(velocity.x, velocity.z).length() > 0.5 and is_on_floor() and step_clock <= 0:
		footsteps.pitch_scale = randf_range(0.8, 1.0)
		footsteps.play()
		step_clock = 0.5
	_update_animation()

func _update_animation() -> void:
	if not is_instance_valid(animation_player) or not active: return
	var horizontal_speed := Vector2(velocity.x, velocity.z).length()
	var wanted := "Idle"
	if horizontal_speed > 2.0: wanted = "Run"
	elif horizontal_speed > 0.15: wanted = "Walk"
	_play_animation(wanted, 0.18)

func _play_animation(requested: String, blend: float = 0.12) -> void:
	if not is_instance_valid(animation_player): return
	var resolved := ""
	for candidate in animation_player.get_animation_list():
		if candidate.to_lower().ends_with(requested.to_lower()):
			resolved = candidate
			break
	if resolved != "" and resolved != current_animation:
		current_animation = resolved
		animation_player.play(resolved, blend)

func _patrol(delta: float) -> void:
	_move_toward(patrol_target, 1.15, delta)
	if global_position.distance_to(patrol_target) < 1.0 or decision_timer <= 0.0:
		decision_timer = randf_range(3.0, 6.0)
		patrol_target = patrol_origin + Vector3(randf_range(-5.0, 5.0), 0, randf_range(-5.0, 5.0))

func _investigate(delta: float, can_see: bool) -> void:
	if can_see:
		_enter_combat()
		return
	search_time -= delta
	_move_toward(last_known_position, 2.2, delta)
	if global_position.distance_to(last_known_position) < 1.5:
		velocity.x = move_toward(velocity.x, 0.0, delta * 6.0)
		velocity.z = move_toward(velocity.z, 0.0, delta * 6.0)
		rotate_y(delta * 0.8)
	if search_time <= 0.0:
		state = AIState.PATROL
		patrol_origin = global_position

func _combat(delta: float, distance: float, can_see: bool) -> void:
	if not can_see:
		search_time -= delta
		if search_time <= 0.0:
			state = AIState.INVESTIGATE
			search_time = 8.0
		return
	search_time = 4.0
	look_at(Vector3(player.global_position.x, global_position.y, player.global_position.z), Vector3.UP)
	if decision_timer <= 0.0:
		decision_timer = randf_range(1.2, 2.6)
		if randf() < 0.65: strafe_direction *= -1.0
	var forward := -global_transform.basis.z
	var right := global_transform.basis.x
	var desired := Vector3.ZERO
	if distance > 20.0: desired += forward
	elif distance < 8.0: desired -= forward
	desired += right * strafe_direction * 0.55
	if _direction_blocked(desired):
		strafe_direction *= -1.0
		desired = right * strafe_direction
	velocity.x = move_toward(velocity.x, desired.normalized().x * 2.6, delta * 10.0)
	velocity.z = move_toward(velocity.z, desired.normalized().z * 2.6, delta * 10.0)
	if attack_timer <= 0.0 and distance < 38.0: _fire_burst(distance)

func _move_toward(target: Vector3, speed: float, delta: float) -> void:
	var waypoint := target
	if NavigationServer3D.map_get_iteration_id(get_world_3d().navigation_map) > 0:
		if path_clock <= 0:
			navigator.target_position = target
			path_clock = 0.5
		waypoint = navigator.get_next_path_position()
	var direction := waypoint - global_position
	direction.y = 0
	if direction.length() > 0.2:
		direction = direction.normalized()
		look_at(global_position + direction, Vector3.UP)
		if _direction_blocked(direction):
			var scene := get_tree().current_scene
			if scene.get("factory") != null:
				for door in scene.factory.get("doors"):
					if not door.opened and not door.locked and global_position.distance_to(door.global_position) < 2:
						door.interact(false)
			direction = Vector3(-direction.z, 0, direction.x)
		velocity.x = move_toward(velocity.x, direction.x * speed, delta * 8.0)
		velocity.z = move_toward(velocity.z, direction.z * speed, delta * 8.0)

func _fire_burst(distance: float) -> void:
	attack_timer = randf_range(0.75, 1.35)
	var rounds := randi_range(2, 4)
	for index in rounds:
		get_tree().create_timer(index * 0.09).timeout.connect(func():
			if active and is_instance_valid(player) and player.raid_active and _can_see_player(global_position.distance_to(player.global_position)):
				_flash_muzzle()
				shot_audio.play()
				var bullet := preload("res://scripts/bullet.gd").new()
				bullet.position = muzzle_flash.global_position
				var target := player.camera.global_position - Vector3.UP * 0.32
				var error := 0.25 + distance * 0.012
				target += Vector3(randf_range(-error, error), randf_range(-error, error), 0)
				bullet.velocity = (target - bullet.position).normalized() * 700
				bullet.shooter = self
				bullet.damage = 42
				bullet.penetration = 22
				get_tree().current_scene.add_child(bullet)
		)

func _flash_muzzle() -> void:
	if not is_instance_valid(muzzle_flash): return
	muzzle_flash.scale = Vector3.ONE * randf_range(0.75, 1.25)
	muzzle_flash.visible = true
	_play_animation("Shoot_OneHanded", 0.06)
	get_tree().create_timer(0.045).timeout.connect(func():
		if is_instance_valid(muzzle_flash): muzzle_flash.visible = false
	)

func _direction_blocked(direction: Vector3) -> bool:
	if direction.length_squared() < 0.01: return false
	var start := global_position + Vector3.UP * 0.8
	var query := PhysicsRayQueryParameters3D.create(start, start + direction.normalized() * 1.3)
	query.exclude = [self]
	query.collision_mask = 1
	if not get_world_3d().direct_space_state.intersect_ray(query).is_empty(): return true
	var ahead := global_position + direction.normalized() * 0.8
	var floor_query := PhysicsRayQueryParameters3D.create(ahead + Vector3.UP * 0.4, ahead - Vector3.UP * 0.7)
	floor_query.collision_mask = 1
	return get_world_3d().direct_space_state.intersect_ray(floor_query).is_empty()

func _can_see_player(distance: float) -> bool:
	if distance > 42.0: return false
	if state == AIState.PATROL and distance > 4.0:
		var direction := (player.global_position - global_position).normalized()
		if direction.dot(-global_basis.z) < 0.25: return false
	var eye := global_position + Vector3.UP * 1.65
	var target := player.camera.global_position
	var query := PhysicsRayQueryParameters3D.create(eye, target)
	query.exclude = [self]
	query.collision_mask = 3
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.collider == player

func _on_gunshot_heard(origin: Vector3, loudness: float) -> void:
	if active and global_position.distance_to(origin) <= loudness and state != AIState.COMBAT:
		last_known_position = origin + Vector3(randf_range(-2.0, 2.0), 0, randf_range(-2.0, 2.0))
		state = AIState.INVESTIGATE
		search_time = 10.0

func _enter_combat() -> void:
	state = AIState.COMBAT
	search_time = 4.0
	for ally in get_tree().get_nodes_in_group("combat_ai"):
		if ally != self and is_instance_valid(ally) and global_position.distance_to(ally.global_position) < 18.0:
			ally.last_known_position = player.global_position
			if ally.state == AIState.PATROL:
				ally.state = AIState.INVESTIGATE
				ally.search_time = 8.0

# 射线命中主 CharacterBody3D 时的保底伤害入口。
func receive_bullet(base_damage: float, hit_position: Vector3, penetration := 28.0) -> void:
	if not active: return
	var height := hit_position.y - global_position.y
	var part := "head" if height > 1.6 else ("thorax" if height > 1.05 else ("stomach" if height > 0.75 else "left_leg"))
	vitals.hit(base_damage, part, penetration)
	_resolve_hit()

func apply_damage(amount: float, part: String) -> void:
	if not active: return
	vitals.hit(amount, "head" if part == "头部" else ("left_leg" if part == "腿部" else "thorax"))
	_resolve_hit()

func _resolve_hit() -> void:
	health = vitals.total()
	last_known_position = player.global_position
	_enter_combat()
	if vitals.dead:
		active = false
		killed.emit(self)
		velocity = Vector3.ZERO
		collision_layer = 0
		for child in get_children():
			if child is Area3D: child.collision_layer = 0
		_play_animation("Death", 0.08)
		set_physics_process(false)
