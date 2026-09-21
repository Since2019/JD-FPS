class_name FPSPlayer
extends CharacterBody3D

signal hud_changed(data: Dictionary)
signal message_requested(text: String, duration: float)
signal gunshot_heard(origin: Vector3, loudness: float)
signal damage_feedback(amount: float)
signal died

const WALK_SPEED := 5.2
const SPRINT_SPEED := 7.4
const JUMP_VELOCITY := 4.8
const MAG_SIZE := 30
const FIRE_INTERVAL := 0.095
const RIFLE_DAMAGE := 200.0

var health := 100.0
var ammo := MAG_SIZE
var reserve_ammo := 120
var can_fire := true
var reloading := false
var aiming := false
var mouse_sensitivity := 0.0022
var stamina := 100.0
var armor := 50.0
var bleeding := false
var crouched := false
var move_time := 0.0
var lean_amount := 0.0
var camera: Camera3D
var weapon: Node3D
var muzzle_flash: OmniLight3D
var fire_timer: Timer
var reload_timer: Timer
var gunshot_player: AudioStreamPlayer3D
var raid_active := true
var flashlight: SpotLight3D
var step_audio: AudioStreamPlayer3D
var step_clock := 0.0

func _ready() -> void:
	_register_extra_inputs()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_build_camera_and_weapon()
	_build_gunshot_audio()
	_build_timers()
	_build_footsteps()
	_emit_hud()

func _register_extra_inputs() -> void:
	for binding in [["crouch", KEY_C], ["lean_left", KEY_Q], ["lean_right", KEY_E]]:
		if not InputMap.has_action(binding[0]):
			InputMap.add_action(binding[0])
			var event := InputEventKey.new()
			event.physical_keycode = binding[1]
			InputMap.action_add_event(binding[0], event)

func _build_camera_and_weapon() -> void:
	camera = Camera3D.new()
	camera.position = Vector3(0, 0.72, 0)
	camera.fov = 78.0
	camera.near = 0.05
	add_child(camera)
	var weapon_fill := OmniLight3D.new()
	weapon_fill.light_energy = 0.35
	weapon_fill.omni_range = 1.5
	weapon_fill.position = Vector3(0, 0.3, -0.3)
	camera.add_child(weapon_fill)
	flashlight = SpotLight3D.new()
	flashlight.position = Vector3(0.2, -0.1, -0.25)
	flashlight.light_color = Color(1, 0.91, 0.74)
	flashlight.light_energy = 3.0
	flashlight.spot_range = 24
	flashlight.spot_angle = 27
	flashlight.shadow_enabled = true
	flashlight.visible = false
	camera.add_child(flashlight)
	weapon = Node3D.new()
	weapon.position = Vector3(0.28, -0.25, -0.55)
	camera.add_child(weapon)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.15, 0.17, 0.16)
	mat.metallic = 0.75
	mat.roughness = 0.3
	_add_weapon_box(Vector3(0.12, 0.14, 0.62), Vector3(0, 0, -0.18), mat)
	_add_weapon_box(Vector3(0.08, 0.18, 0.20), Vector3(0, -0.14, -0.10), mat, Vector3(-12, 0, 0))
	_add_weapon_box(Vector3(0.10, 0.10, 0.34), Vector3(0, 0.01, 0.27), mat)
	_add_weapon_box(Vector3(0.09, 0.025, 0.35), Vector3(0, 0.085, -0.05), mat)
	# Ventilated handguard, receiver rail and open iron sights.
	for z in [-0.26, -0.34, -0.42, -0.50]:
		_add_weapon_box(Vector3(0.14, 0.022, 0.025), Vector3(0, 0.085, z), mat)
	for x in [-0.035, 0.035]:
		_add_weapon_box(Vector3(0.012, 0.035, 0.025), Vector3(x, 0.12, 0.10), mat)
	_add_weapon_box(Vector3(0.012, 0.065, 0.025), Vector3(0, 0.11, -0.68), mat)
	var hand_mat := StandardMaterial3D.new()
	hand_mat.albedo_color = Color(0.30, 0.27, 0.20)
	hand_mat.roughness = 1.0
	_add_weapon_box(Vector3(0.10, 0.12, 0.27), Vector3(0.13, -0.10, -0.24), hand_mat, Vector3(0, 0, -12))
	var barrel := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.025
	cyl.bottom_radius = 0.025
	cyl.height = 0.48
	barrel.mesh = cyl
	barrel.rotation_degrees.x = 90
	barrel.position = Vector3(0, 0.02, -0.67)
	barrel.material_override = mat
	weapon.add_child(barrel)
	muzzle_flash = OmniLight3D.new()
	muzzle_flash.light_color = Color(1.0, 0.62, 0.22)
	muzzle_flash.light_energy = 3.5
	muzzle_flash.omni_range = 3.0
	muzzle_flash.position = Vector3(0, 0, -0.94)
	muzzle_flash.visible = false
	weapon.add_child(muzzle_flash)

func _add_weapon_box(size: Vector3, pos: Vector3, material: Material, rot := Vector3.ZERO) -> void:
	var part := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	part.mesh = mesh
	part.position = pos
	part.rotation_degrees = rot
	part.material_override = material
	weapon.add_child(part)

func _build_gunshot_audio() -> void:
	gunshot_player = AudioStreamPlayer3D.new()
	gunshot_player.unit_size = 7.0
	gunshot_player.max_distance = 90.0
	gunshot_player.volume_db = -2.0
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 44100
	stream.stereo = false
	var sample_count := 7938 # 约 180 ms
	var pcm := PackedByteArray()
	pcm.resize(sample_count * 2)
	for index in sample_count:
		var time := float(index) / 44100.0
		var decay := exp(-time * 27.0)
		var blast := sin(TAU * 82.0 * time) * exp(-time * 34.0)
		var crack := randf_range(-1.0, 1.0) * decay
		var tail := randf_range(-0.45, 0.45) * exp(-time * 11.0)
		var sample := clampf((crack * 0.72 + blast * 0.58 + tail * 0.20) * 0.82, -1.0, 1.0)
		pcm.encode_s16(index * 2, int(sample * 32767.0))
	stream.data = pcm
	gunshot_player.stream = stream
	camera.add_child(gunshot_player)

func _build_timers() -> void:
	fire_timer = Timer.new()
	fire_timer.one_shot = true
	fire_timer.wait_time = FIRE_INTERVAL
	fire_timer.timeout.connect(func(): can_fire = true)
	add_child(fire_timer)
	reload_timer = Timer.new()
	reload_timer.one_shot = true
	reload_timer.wait_time = 1.65
	reload_timer.timeout.connect(_finish_reload)
	add_child(reload_timer)

func _unhandled_input(event: InputEvent) -> void:
	if not raid_active: return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_T:
		flashlight.visible = not flashlight.visible
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		camera.rotation.x = clamp(camera.rotation.x - event.relative.y * mouse_sensitivity, deg_to_rad(-82), deg_to_rad(82))
	if event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED

func _physics_process(delta: float) -> void:
	if not raid_active: return
	if bleeding:
		health = maxf(health - delta * 0.7, 0.0)
		if health <= 0:
			raid_active = false
			died.emit()
			return
	var was_grounded := is_on_floor()
	if not was_grounded:
		velocity.y -= 14.0 * delta
	if Input.is_action_just_pressed("jump") and was_grounded:
		velocity.y = JUMP_VELOCITY
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input.x, 0, input.y)).normalized()
	crouched = Input.is_action_pressed("crouch")
	var wants_sprint := Input.is_action_pressed("sprint") and input.y < 0 and stamina > 1.0 and not crouched
	var speed := SPRINT_SPEED if wants_sprint else (3.0 if crouched else WALK_SPEED)
	if wants_sprint and input.length() > 0.1:
		stamina = maxf(stamina - 18.0 * delta, 0.0)
	else:
		stamina = minf(stamina + 12.0 * delta, 100.0)
	# 地面上才能主动改变水平速度；离地后只保留起跳时的惯性。
	if was_grounded:
		velocity.x = move_toward(velocity.x, direction.x * speed, 24.0 * delta)
		velocity.z = move_toward(velocity.z, direction.z * speed, 24.0 * delta)
	move_and_slide()
	var horizontal_speed := Vector2(velocity.x, velocity.z).length()
	step_clock -= delta
	if is_on_floor() and horizontal_speed > 0.5 and step_clock <= 0:
		step_audio.pitch_scale = randf_range(0.85, 1.15)
		step_audio.volume_db = -22 if crouched else (-8 if wants_sprint else -14)
		step_audio.play()
		step_clock = 0.28 if wants_sprint else (0.65 if crouched else 0.43)
		gunshot_heard.emit(global_position, 5.0 if crouched else (20.0 if wants_sprint else 10.0))
	if is_on_floor() and horizontal_speed > 0.2:
		move_time += delta * (12.0 if wants_sprint else 8.0)
	var target_height := 0.30 if crouched else 0.72
	var bob := sin(move_time) * 0.018 * clampf(horizontal_speed / WALK_SPEED, 0.0, 1.4)
	# 空中禁止左右探头，并平滑回正，避免滞留倾斜姿态。
	var lean_target := 0.0
	if is_on_floor():
		lean_target = -1.0 if Input.is_action_pressed("lean_left") else (1.0 if Input.is_action_pressed("lean_right") else 0.0)
	lean_amount = lerpf(lean_amount, lean_target, 10.0 * delta)
	camera.position.y = lerpf(camera.position.y, target_height + bob, 12.0 * delta)
	camera.position.x = lerpf(camera.position.x, lean_amount * 0.28, 10.0 * delta)
	camera.rotation.z = lerpf(camera.rotation.z, deg_to_rad(-lean_amount * 8.0), 10.0 * delta)
	aiming = Input.is_action_pressed("aim")
	camera.fov = lerp(camera.fov, 58.0 if aiming else 78.0, 12.0 * delta)
	weapon.position = weapon.position.lerp(Vector3(0.0, -0.20, -0.48) if aiming else Vector3(0.28, -0.25, -0.55), 12.0 * delta)
	weapon.rotation.x = lerpf(weapon.rotation.x, sin(move_time * 0.5) * 0.008 if horizontal_speed > 0.2 else 0.0, 8.0 * delta)
	if Input.is_action_pressed("fire") and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_fire()
	if Input.is_action_just_pressed("reload"):
		_start_reload()
	_emit_hud()

func _fire() -> void:
	if not can_fire or reloading:
		return
	if ammo <= 0:
		message_requested.emit("弹匣为空，按 R 换弹", 1.0)
		can_fire = false
		fire_timer.start(0.25)
		return
	ammo -= 1
	gunshot_heard.emit(global_position, 55.0)
	gunshot_player.pitch_scale = randf_range(0.96, 1.04)
	gunshot_player.play()
	can_fire = false
	fire_timer.start()
	muzzle_flash.visible = true
	get_tree().create_timer(0.035).timeout.connect(func(): if is_instance_valid(muzzle_flash): muzzle_flash.visible = false)
	var spread := 0.0025 if aiming else 0.009
	var direction := -camera.global_transform.basis.z
	direction += camera.global_transform.basis.x * randf_range(-spread, spread)
	direction += camera.global_transform.basis.y * randf_range(-spread, spread)
	var query := PhysicsRayQueryParameters3D.create(camera.global_position, camera.global_position + direction.normalized() * 180.0)
	query.exclude = [self]
	query.collision_mask = 5
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit:
		var collider: Object = hit.collider
		if collider.has_method("receive_bullet"):
			var distance: float = camera.global_position.distance_to(hit.position)
			# 高致死规则：即使远距离命中四肢，步枪弹也足以造成致命伤。
			collider.receive_bullet(RIFLE_DAMAGE * clamp(1.0 - max(distance - 35.0, 0.0) / 250.0, 0.82, 1.0), hit.position)
		_spawn_impact(hit.position, hit.normal)
	camera.rotation.x = clamp(camera.rotation.x + deg_to_rad(randf_range(0.55, 0.9)), deg_to_rad(-82), deg_to_rad(82))
	weapon.rotation.z = randf_range(-0.018, 0.018)
	get_tree().create_tween().tween_property(weapon, "rotation:z", 0.0, 0.08)
	_emit_hud()

func _spawn_impact(at: Vector3, normal: Vector3) -> void:
	var impact := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 0.035
	mesh.height = 0.07
	impact.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(1.0, 0.58, 0.18)
	material.emission_enabled = true
	material.emission = Color(1.0, 0.25, 0.02)
	impact.material_override = material
	get_tree().current_scene.add_child(impact)
	impact.global_position = at + normal * 0.02
	get_tree().create_timer(0.12).timeout.connect(impact.queue_free)

func _start_reload() -> void:
	if reloading or ammo == MAG_SIZE or reserve_ammo <= 0:
		return
	reloading = true
	message_requested.emit("换弹中…", 1.5)
	reload_timer.start()

func _finish_reload() -> void:
	var needed := MAG_SIZE - ammo
	var loaded: int = mini(needed, reserve_ammo)
	ammo += loaded
	reserve_ammo -= loaded
	reloading = false
	_emit_hud()

func take_damage(amount: float, _part := "thorax", _penetration := 28.0) -> void:
	if not raid_active: return
	var absorbed := minf(armor, amount * 0.55)
	armor -= absorbed
	health = maxf(health - (amount - absorbed), 0.0)
	damage_feedback.emit(amount - absorbed)
	camera.rotation.z += deg_to_rad(randf_range(-1.8, 1.8))
	var hit_tween := create_tween()
	hit_tween.tween_property(camera, "rotation:z", deg_to_rad(-lean_amount * 8.0), 0.16)
	if health < 55.0 and not bleeding and randf() < 0.22:
		bleeding = true
		message_requested.emit("失血状态：生命正在缓慢下降", 2.0)
	_emit_hud()
	if health <= 0:
		raid_active = false
		died.emit()

func _build_footsteps() -> void:
	step_audio = AudioStreamPlayer3D.new()
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	var pcm := PackedByteArray()
	pcm.resize(4400)
	for i in 2200:
		var t := float(i) / 22050
		var sample := (randf_range(-1, 1) * 0.35 + sin(t * TAU * 110) * 0.65) * exp(-t * 55)
		pcm.encode_s16(i * 2, int(sample * 20000))
	stream.data = pcm
	step_audio.stream = stream
	camera.add_child(step_audio)

func add_ammo(amount: int) -> void:
	reserve_ammo += amount
	_emit_hud()

func _emit_hud() -> void:
	hud_changed.emit({"health": int(health), "armor": int(armor), "stamina": int(stamina), "bleeding": bleeding, "ammo": ammo, "reserve": reserve_ammo})
