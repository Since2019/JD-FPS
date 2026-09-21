extends "res://scripts/player.gd"

# Tunable simulation values; these are not extracted EFT internals.
var vitals := RaidVitals.new()
var magazines: Array[int] = [30, 30, 30]
var chambered := true
var loose_rounds := 60
var carry_weight := 23.0
var arm_stamina := 100.0
var walk_fraction := 1.0
var stance := 0 # 0 standing, 1 crouched, 2 prone
var sprinting := false
var inventory_open := false
var interacting := false
var action_kind := ""
var action_left := 0.0
var action_duration := 0.0
var recovery_delay := 0.0
var sprint_lock := 0.0
var recoil := Vector2.ZERO
var recoil_velocity := Vector2.ZERO
var aim_pitch := 0.0
var breath_clock := 0.0
var auto_fire := true
var reload_pending := 0.0
var quick_reload := false
var grenade_count := 2
var reload_mag_index := -1
var magazine_mesh: MeshInstance3D
var body_shape: CollisionShape3D
signal treatment_finished
signal magazine_dropped(rounds: int)
signal inventory_toggled(open: bool)

func _ready() -> void:
	super._ready()
	ammo = 29
	health = 440
	body_shape = get_child(0) as CollisionShape3D
	# The second procedural weapon piece is the visible magazine.
	magazine_mesh = weapon.get_child(1) as MeshInstance3D
	for binding in [["prone", KEY_X], ["inventory", KEY_TAB], ["fire_mode", KEY_B], ["grenade", KEY_G], ["pack_mag", KEY_P], ["hold_breath", KEY_ALT], ["medical", KEY_H]]:
		if not InputMap.has_action(binding[0]):
			InputMap.add_action(binding[0])
			var key := InputEventKey.new()
			key.physical_keycode = binding[1]
			InputMap.action_add_event(binding[0], key)
	# Some Windows input/remote-desktop paths report logical keys without a scan code.
	for action in InputMap.get_actions():
		for binding in InputMap.action_get_events(action):
			if binding is InputEventKey and binding.physical_keycode != 0:
				var logical := InputEventKey.new()
				logical.keycode = binding.physical_keycode
				if not InputMap.action_has_event(action, logical): InputMap.action_add_event(action, logical)
	_sync_state()

func _input(event: InputEvent) -> void:
	# Tab is also GUI focus navigation; intercept it before Control consumes it.
	if is_processing_unhandled_input() and raid_active and (event.is_action_pressed("inventory") or event.is_action_pressed("ui_cancel")):
		_unhandled_input(event)
		get_viewport().set_input_as_handled()

func _unhandled_input(event: InputEvent) -> void:
	if not raid_active: return
	if event.is_action_pressed("inventory"):
		inventory_open = not inventory_open
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if inventory_open else Input.MOUSE_MODE_CAPTURED
		inventory_toggled.emit(inventory_open)
		return
	if event.is_action_pressed("ui_cancel"):
		if action_kind == "pack":
			cancel_action()
			return
		inventory_open = not inventory_open
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if inventory_open else Input.MOUSE_MODE_CAPTURED
		inventory_toggled.emit(inventory_open)
		return
	if event.is_action_pressed("pack_mag"):
		if action_kind == "pack": cancel_action()
		elif loose_rounds > 0: begin_action("pack", 0.65)
	if inventory_open: return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var sensitivity := mouse_sensitivity * (0.7 if aiming else 1.0)
		rotate_y(-event.relative.x * sensitivity)
		aim_pitch = clampf(aim_pitch - event.relative.y * sensitivity, -1.4, 1.4)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP: walk_fraction = minf(1.0, walk_fraction + 0.1)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN: walk_fraction = maxf(0.2, walk_fraction - 0.1)
	if event.is_action_pressed("crouch"): _change_stance(0 if stance == 1 else 1)
	if event.is_action_pressed("prone"): _change_stance(0 if stance == 2 else 2)
	if event.is_action_pressed("fire_mode"):
		auto_fire = not auto_fire
		message_requested.emit("射击模式：" + ("全自动" if auto_fire else "半自动"), 1.4)
	if event is InputEventKey and event.pressed and not event.echo and (event.physical_keycode == KEY_T or event.keycode == KEY_T):
		if event.alt_pressed: begin_action("check_chamber", 0.9)
		else: flashlight.visible = not flashlight.visible
	if event is InputEventKey and event.pressed and not event.echo and (event.physical_keycode == KEY_R or event.keycode == KEY_R):
		if event is InputEventKey and event.alt_pressed:
			begin_action("check_mag", 1.1)
		elif reload_pending > 0:
			reload_pending = 0
			_start_reload_mode(true)
		else: reload_pending = 0.24
	if event.is_action_pressed("grenade") and grenade_count > 0: begin_action("grenade", 0.85)

func _change_stance(wanted: int) -> void:
	var heights := [1.8, 1.15, 0.65]
	var new_height: float = heights[wanted]
	if new_height > (body_shape.shape as CapsuleShape3D).height:
		var query := PhysicsShapeQueryParameters3D.new()
		var capsule := CapsuleShape3D.new()
		capsule.radius = 0.32
		capsule.height = new_height
		query.shape = capsule
		query.transform = Transform3D(Basis.IDENTITY, global_position + Vector3.UP * ((new_height - 1.8) * 0.5 + 0.03))
		query.margin = 0.001
		query.exclude = [self]
		query.collision_mask = 1
		if not get_world_3d().direct_space_state.intersect_shape(query).is_empty(): return
	stance = wanted
	(body_shape.shape as CapsuleShape3D).height = new_height
	body_shape.position.y = (new_height - 1.8) * 0.5
	crouched = stance != 0

func begin_action(kind: String, duration: float) -> bool:
	if action_kind != "" or sprinting or not raid_active: return false
	action_kind = kind
	action_left = duration
	action_duration = duration
	return true

func _physics_process(delta: float) -> void:
	if not raid_active: return
	vitals.tick(delta)
	if vitals.dead:
		raid_active = false
		died.emit()
		return
	if reload_pending > 0:
		reload_pending -= delta
		if reload_pending <= 0: _start_reload_mode(false)
	if action_kind != "":
		action_left -= delta
		if action_left <= 0: _finish_action()
	recovery_delay = maxf(0, recovery_delay - delta)
	sprint_lock = maxf(0, sprint_lock - delta)
	var grounded := is_on_floor()
	if not grounded: velocity.y -= 16 * delta
	var movement := Vector2.ZERO if inventory_open else Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var burden := clampf((carry_weight - 24) / 35, 0, 0.65)
	var was_sprinting := sprinting
	sprinting = not inventory_open and Input.is_action_pressed("sprint") and movement.y < -0.3 and stamina > 3 and stance == 0 and action_kind == "" and not vitals.leg_injured()
	if was_sprinting and not sprinting: sprint_lock = 0.28
	aiming = not inventory_open and not interacting and Input.is_action_pressed("aim") and not sprinting and action_kind == "" and sprint_lock <= 0
	var speed := (5.8 if sprinting else 2.6 * walk_fraction) * (1 - burden)
	if stance == 1: speed *= 0.58
	if stance == 2: speed *= 0.22
	if aiming: speed *= 0.65
	if vitals.leg_injured(): speed *= 0.48
	if movement.y > 0: speed *= 0.75
	if action_kind != "": speed *= 0.65
	var direction := (basis * Vector3(movement.x, 0, movement.y)).normalized()
	if grounded:
		var acceleration := (8.5 if movement.length() > 0 else 11.0) * (1 - burden * 0.6)
		velocity.x = move_toward(velocity.x, direction.x * speed, acceleration * delta)
		velocity.z = move_toward(velocity.z, direction.z * speed, acceleration * delta)
		if not inventory_open and Input.is_action_just_pressed("jump") and stance == 0 and stamina >= 15 and not vitals.leg_injured():
			velocity.y = 4.2
			stamina -= 15
			recovery_delay = 1.5
	move_and_slide()
	if sprinting:
		stamina = maxf(0, stamina - (13 + burden * 20) * delta)
		recovery_delay = 1.5
	elif recovery_delay <= 0:
		stamina = minf(100, stamina + (10 if movement.length() < 0.1 else 5) * delta)
	if aiming: arm_stamina = maxf(0, arm_stamina - (4.5 if stance == 0 else 2.5) * delta)
	else: arm_stamina = minf(100, arm_stamina + 12 * delta)
	var speed_now := Vector2(velocity.x, velocity.z).length()
	step_clock -= delta
	if grounded and speed_now > 0.2 and step_clock <= 0:
		step_audio.pitch_scale = randf_range(0.88, 1.12)
		step_audio.volume_db = -25 if stance > 0 else (-7 if sprinting else -16)
		step_audio.play()
		step_clock = 0.29 if sprinting else 0.48 / maxf(walk_fraction, 0.4)
		gunshot_heard.emit(global_position, (22 if sprinting else 9) * (0.4 if stance > 0 else walk_fraction))
	_update_view(delta, speed_now)
	if not inventory_open and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		if (Input.is_action_pressed("fire") if auto_fire else Input.is_action_just_pressed("fire")): _fire()
	_sync_state()

func _update_view(delta: float, speed_now: float) -> void:
	move_time += delta * speed_now * 2.2
	breath_clock += delta
	var target_height: float = [0.72, 0.08, -0.46][stance]
	var bob: float = sin(move_time) * 0.014 * minf(speed_now, 3) * (0.15 if aiming else 1)
	var target_lean := 0.0
	if is_on_floor() and not sprinting and not inventory_open:
		target_lean = Input.get_axis("lean_left", "lean_right")
	var head := global_position + Vector3.UP * target_height
	var cast := PhysicsRayQueryParameters3D.create(head, head + global_basis.x * target_lean * 0.42)
	cast.collision_mask = 1
	var wall := get_world_3d().direct_space_state.intersect_ray(cast)
	if wall: target_lean *= clampf((head.distance_to(wall.position) - 0.13) / 0.42, 0, 1)
	lean_amount = lerpf(lean_amount, target_lean, 1 - exp(-9 * delta))
	camera.position = camera.position.lerp(Vector3(lean_amount * 0.27, target_height + bob, 0), 1 - exp(-12 * delta))
	recoil_velocity += (-recoil * 85 - recoil_velocity * 17) * delta
	recoil += recoil_velocity * delta
	var sway := (0.0007 + (1 - arm_stamina / 100) * 0.005) * (2 if vitals.arm_injured() else 1)
	if Input.is_action_pressed("hold_breath") and arm_stamina > 15 and aiming:
		sway *= 0.15
		arm_stamina -= delta * 6
	camera.rotation = Vector3(aim_pitch + recoil.x + sin(breath_clock * 1.8) * sway, recoil.y, deg_to_rad(-lean_amount * 7))
	camera.fov = lerpf(camera.fov, 62 if aiming else 76, 1 - exp(-9 * delta))
	var rest := Vector3(0, -0.12, -0.48) if aiming else Vector3(0.24, -0.25, -0.53)
	var tilt := Vector3.ZERO
	if sprinting:
		rest += Vector3(0.08, -0.16, 0.12)
		tilt = Vector3(-0.45, 0.35, 0.2)
	if action_kind != "":
		var progress := 1 - action_left / maxf(action_duration, 0.01)
		var motion := sin(progress * PI)
		rest += Vector3(-0.06, -0.22 * motion, 0.15 * motion)
		tilt = Vector3(-0.3 * motion, 0.15 * motion, -0.5 * motion)
		if is_instance_valid(magazine_mesh): magazine_mesh.position.y = -0.14 - 0.22 * motion
	else:
		if is_instance_valid(magazine_mesh): magazine_mesh.position.y = -0.14
	weapon.position = weapon.position.lerp(rest + Vector3(0, 0, recoil.x * 0.7), 1 - exp(-12 * delta))
	weapon.rotation = weapon.rotation.lerp(tilt, 1 - exp(-12 * delta))

func _fire() -> void:
	if not raid_active or not can_fire or action_kind != "" or sprinting or sprint_lock > 0 or inventory_open or interacting: return
	if not chambered:
		message_requested.emit("空膛", 0.8)
		can_fire = false
		fire_timer.start(0.25)
		return
	chambered = false
	if ammo > 0:
		ammo -= 1
		chambered = true
	can_fire = false
	fire_timer.start(0.092)
	gunshot_player.pitch_scale = randf_range(0.97, 1.03)
	gunshot_player.play()
	gunshot_heard.emit(global_position, 65)
	muzzle_flash.visible = true
	get_tree().create_timer(0.04).timeout.connect(func(): if is_instance_valid(muzzle_flash): muzzle_flash.visible = false)
	var spread := (0.0012 if aiming else 0.012) + Vector2(velocity.x, velocity.z).length() * 0.0015
	var aim_direction := -camera.global_basis.z
	aim_direction += camera.global_basis.x * randf_range(-spread, spread) + camera.global_basis.y * randf_range(-spread, spread)
	var query := PhysicsRayQueryParameters3D.create(camera.global_position, camera.global_position + aim_direction.normalized() * 150)
	query.collision_mask = 5
	query.exclude = [self]
	var target := get_world_3d().direct_space_state.intersect_ray(query)
	var destination: Vector3 = target.position if target else query.to
	# Muzzle obstruction is resolved before the ballistic ray: sights cannot shoot through cover.
	var muzzle := weapon.to_global(Vector3(0, 0.02, -0.9))
	var obstruction := PhysicsRayQueryParameters3D.create(camera.global_position, muzzle)
	obstruction.collision_mask = 1
	var blocked := get_world_3d().direct_space_state.intersect_ray(obstruction)
	if blocked: _spawn_impact(blocked.position, blocked.normal)
	else:
		var bullet := preload("res://scripts/bullet.gd").new()
		bullet.position = muzzle
		bullet.velocity = (destination - muzzle).normalized() * 880
		bullet.shooter = self
		get_tree().current_scene.add_child(bullet)
	recoil_velocity += Vector2(0.23 if aiming else 0.32, randf_range(-0.07, 0.07)) * (1.35 if vitals.arm_injured() else 1)
	arm_stamina = maxf(0, arm_stamina - 1.1)
	_sync_state()

func _start_reload() -> void:
	_start_reload_mode(false)

func _start_reload_mode(quick: bool) -> void:
	if action_kind != "" or magazines.is_empty(): return
	reload_mag_index = 0
	for i in magazines.size():
		if magazines[i] > magazines[reload_mag_index]: reload_mag_index = i
	if ammo >= magazines[reload_mag_index] and chambered: return
	quick_reload = quick
	if begin_action("reload", 1.8 if quick else (2.8 if chambered else 3.4)):
		reloading = true

func _finish_reload() -> void:
	if reload_mag_index < 0 or reload_mag_index >= magazines.size():
		reloading = false
		return
	var next: int = magazines.pop_at(reload_mag_index)
	if quick_reload: magazine_dropped.emit(ammo)
	else: magazines.append(ammo)
	ammo = next
	if not chambered and ammo > 0:
		ammo -= 1
		chambered = true
	reloading = false
	reload_mag_index = -1

func _finish_action() -> void:
	var done := action_kind
	action_kind = ""
	match done:
		"reload": _finish_reload()
		"check_mag": message_requested.emit("弹匣：" + ("满" if ammo >= 28 else "大半" if ammo >= 20 else "约一半" if ammo >= 12 else "少量" if ammo > 0 else "空"), 2)
		"check_chamber": message_requested.emit("膛内有弹" if chambered else "空膛", 2)
		"medical":
			vitals.heal()
			treatment_finished.emit()
		"bandage":
			vitals.wounds.clear()
			treatment_finished.emit()
		"pack":
			for i in magazines.size():
				if magazines[i] < 30 and loose_rounds > 0:
					magazines[i] += 1
					loose_rounds -= 1
					begin_action("pack", 0.65)
					break
		"grenade":
			grenade_count -= 1
			var grenade := preload("res://scripts/grenade.gd").new()
			grenade.position = camera.global_position - camera.global_basis.z * 0.45
			grenade.linear_velocity = -camera.global_basis.z * 12 + Vector3.UP * 2
			grenade.shooter = self
			get_tree().current_scene.add_child(grenade)

func cancel_action() -> void:
	action_kind = ""
	action_left = 0
	reloading = false
	reload_pending = 0

func take_damage(amount: float, part := "thorax", penetration := 28.0) -> void:
	if not raid_active: return
	var dealt := vitals.hit(amount, part, penetration)
	damage_feedback.emit(dealt)
	stamina = maxf(0, stamina - dealt * 0.2)
	_sync_state()
	if vitals.dead:
		raid_active = false
		died.emit()

func receive_bullet(amount: float, at: Vector3, penetration := 28.0) -> void:
	var height := at.y - (global_position.y - 0.9)
	var total_height: float = [1.8, 1.15, 0.65][stance]
	var fraction := height / total_height
	var part := "head" if fraction > 0.86 else ("thorax" if fraction > 0.56 else ("stomach" if fraction > 0.4 else ("left_leg" if randf() < 0.5 else "right_leg")))
	take_damage(amount, part, penetration)

func add_ammo(amount: int) -> void:
	loose_rounds += amount
	_sync_state()

func _sync_state() -> void:
	health = vitals.total()
	armor = vitals.armor
	bleeding = not vitals.wounds.is_empty()
	reserve_ammo = loose_rounds
	_emit_hud()

func _emit_hud() -> void:
	hud_changed.emit({"health": int(health), "armor": int(armor), "stamina": int(stamina), "bleeding": bleeding, "ammo": ammo, "reserve": reserve_ammo})
