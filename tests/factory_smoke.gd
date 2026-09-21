extends SceneTree
var game
var failures: Array[String] = []
var checks := 0
func _initialize() -> void: call_deferred("run")
func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures.append(label)
	print(("PASS " if value else "FAIL ") + label)
func frames(n: int) -> void:
	for i in n: await physics_frame
func place(at: Vector3, yaw := 0.0) -> void:
	game.player.position = at
	game.player.velocity = Vector3.ZERO
	game.player.rotation = Vector3(0, yaw, 0)
	game.player.aim_pitch = 0
	await frames(5)
func walk(action: String, n: int) -> void:
	Input.action_press(action)
	await frames(n)
	Input.action_release(action)
	await frames(15)
func aim_at(at: Vector3) -> void:
	var dir: Vector3 = at - game.player.camera.global_position
	game.player.rotation.y = atan2(-dir.x, -dir.z)
	game.player.aim_pitch = atan2(dir.y, Vector2(dir.x, dir.z).length())
	await frames(3)
func run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	game.raid_save_path = "user://classic_test_raid.json"
	await frames(30)
	var p = game.player
	check(p.is_on_floor() and p.health == 440, "spawn valid and all seven body regions intact")
	for physical in [true, false]:
		var key := InputEventKey.new()
		if physical: key.physical_keycode = KEY_TAB
		else: key.keycode = KEY_TAB
		key.pressed = true
		Input.parse_input_event(key)
		await frames(3)
		check(p.inventory_open and game.pack_panel.visible, "Tab opens inventory (%s keys)" % ("physical" if physical else "logical"))
		key = InputEventKey.new()
		if physical: key.physical_keycode = KEY_TAB
		else: key.keycode = KEY_TAB
		key.pressed = false
		Input.parse_input_event(key)
		await frames(1)
		key = InputEventKey.new()
		if physical: key.physical_keycode = KEY_TAB
		else: key.keycode = KEY_TAB
		key.pressed = true
		Input.parse_input_event(key)
		await frames(3)
		check(not p.inventory_open, "Tab closes inventory (%s keys)" % ("physical" if physical else "logical"))
		key = InputEventKey.new()
		if physical: key.physical_keycode = KEY_TAB
		else: key.keycode = KEY_TAB
		key.pressed = false
		Input.parse_input_event(key)
	for pair in [[KEY_R, "check_mag"], [KEY_T, "check_chamber"]]:
		var key := InputEventKey.new()
		key.keycode = pair[0]
		key.alt_pressed = true
		key.pressed = true
		Input.parse_input_event(key)
		await frames(3)
		check(p.action_kind == pair[1], "Alt modifier starts " + pair[1])
		key = InputEventKey.new()
		key.keycode = pair[0]
		key.alt_pressed = true
		key.pressed = false
		Input.parse_input_event(key)
		p.cancel_action()
	var navpath := NavigationServer3D.map_get_path(game.get_world_3d().navigation_map, Vector3(14, 0, -22), Vector3(-20, 0, 15), true)
	check(navpath.size() > 2 and navpath[-1].distance_to(Vector3(-20, 0, 15)) < 1, "navigation connects the eastern and tank halls around geometry")
	# Real traversal from the ground, including both flights and the facade landing.
	await place(Vector3(-11, 1, 23))
	await walk("move_forward", 660)
	print("STAIR_POSITION ", p.position)
	check(p.position.y > 7 and p.position.z < 0, "walk both flights to third floor")
	await place(Vector3(-11, 7.3, -2))
	await walk("move_right", 100)
	check(p.position.x > -8 and p.position.y > 7, "third floor landing enters office corridor")
	await place(Vector3(-11, 7.3, -2))
	await walk("move_left", 150)
	check(p.position.x < -15 and p.position.y > 7, "third floor connects to overhead tank catwalk")
	await place(Vector3(18, 1, 19))
	await walk("move_back", 400)
	print("TUNNEL_POSITION ", p.position)
	check(p.position.y < -2 and p.position.z > 29, "descend eastern stair into real basement")
	await walk("move_left", 800)
	check(p.position.x < -15 and p.position.y < -2, "underground cross passage connects eastern and western halls")
	# Inertia and stance collision.
	await place(Vector3(6, 1, -15))
	Input.action_press("move_forward")
	await frames(12)
	check(p.velocity.z < -0.1 and p.velocity.z > -2.6, "movement accelerates rather than snapping to full speed")
	Input.action_release("move_forward")
	await frames(30)
	p._change_stance(1)
	check((p.body_shape.shape as CapsuleShape3D).height < 1.3, "crouch changes physical collision capsule")
	p._change_stance(0)
	check(p.stance == 0, "standing up works with clearance")
	# Every round is conserved by a tactical reload, including the chamber.
	p.ammo = 8
	p.magazines.assign([30, 17])
	p.chambered = true
	p._start_reload_mode(false)
	await frames(190)
	check(p.ammo == 30 and p.magazines == [17, 8] and p.chambered, "tactical reload preserves partial magazine and chamber")
	p.ammo = 0
	p.chambered = false
	p._start_reload_mode(false)
	await frames(220)
	check(p.ammo == 16 and p.chambered and 0 in p.magazines, "empty reload chambers one round from replacement magazine")
	p.ammo = 4
	var loot_before: int = game.factory.loot.size()
	p.magazines.assign([30])
	p._start_reload_mode(true)
	await frames(120)
	check(p.ammo == 30 and p.magazines.is_empty() and game.factory.loot.size() == loot_before + 1, "quick reload drops actual partial magazine into world")
	p.magazines.assign([28])
	p.loose_rounds = 2
	p.begin_action("pack", 0.65)
	await frames(140)
	check(p.magazines == [30] and p.loose_rounds == 0, "packing consumes individual loose rounds")
	# Injury and medical state.
	p.take_damage(40, "left_leg", 50)
	check(p.bleeding and not p.vitals.dead and p.vitals.hp.left_leg < 30, "limb damage causes bleeding without arbitrary instant death")
	var hp_before: float = p.vitals.hp.left_leg
	game.selected_id = game.backpack.find_item("医疗包")
	game._use_selected()
	await frames(255)
	check(not p.bleeding and p.vitals.hp.left_leg > hp_before and not game.backpack.has("医疗包"), "medical action completes before consuming item and healing")
	# Search is based on gaze and actual container, without guaranteed access through cover.
	await place(Vector3(-28, 1, -26))
	await aim_at(game.factory.loot[0].position)
	Input.action_press("interact")
	await frames(170)
	Input.action_release("interact")
	check(game.factory.loot[0].taken, "hold F searches insertion duffle")
	# Projectile sweeps hit visible anatomy; collision at the muzzle blocks firing over cover.
	await place(Vector3(15, 1, -21))
	var enemy = get_nodes_in_group("combat_ai")[0]
	enemy.position = Vector3(15, 0, -28)
	enemy.active = true
	enemy.set_physics_process(false)
	await aim_at(enemy.position + Vector3.UP * 1.73)
	Input.action_press("aim")
	await frames(35)
	var cover = game.factory._box("test muzzle cover", Vector3(1, 0.5, 0.15), p.camera.global_position - p.camera.global_basis.z * 0.8 - Vector3.UP * 0.3, "steel")
	await frames(3)
	p._fire()
	await frames(12)
	check(enemy.active and enemy.vitals.total() == 440, "muzzle obstruction prevents shooting through close cover")
	cover.queue_free()
	await frames(4)
	await aim_at(enemy.position + Vector3.UP * 1.73)
	p._fire()
	await frames(15)
	check(not enemy.active and game.kills == 1, "swept ballistic projectile can kill with a head hit")
	check(game.factory.loot.back().title == "尸体武器", "enemy death produces searchable body equipment")
	Input.action_release("aim")
	# Blast blocked by the solid insertion wall.
	enemy = get_nodes_in_group("combat_ai")[1]
	enemy.position = Vector3(-29, 0, -21.5)
	enemy.active = true
	enemy.set_physics_process(false)
	await frames(3)
	var grenade = load("res://scripts/grenade.gd").new()
	grenade.position = Vector3(-29, 0.3, -18.5)
	game.add_child(grenade)
	grenade.explode()
	await frames(3)
	check(enemy.vitals.total() == 440, "solid wall shields actors from grenade blast")
	await place(Vector3(-29, 1, -19))
	await aim_at(Vector3(-29, 1, -20.2))
	check(not game._visible_interaction(Vector3(-29, 1, -20.2)), "even a nearby thin wall blocks interaction")
	# Door passage: blocked when closed, traversable after interaction.
	await place(Vector3(22, 1, -19))
	await walk("move_forward", 80)
	check(p.position.z > -21, "closed Gate 3 door blocks player capsule")
	var gate = null
	for door in game.factory.doors:
		if door.title == "Gate 3 外门": gate = door
	gate.interact(false)
	await frames(40)
	await walk("move_forward", 90)
	print("GATE_POSITION ", p.position)
	check(p.position.z < -22, "opened Gate 3 door allows passage")
	# Free exit and keyed exit, with interruption and correct settlement.
	await place(Vector3(-33.5, 1, -29))
	await frames(30)
	check(game.extraction_progress == 0, "Gate 0 requires the Factory exit key")
	await place(Vector3(22, 1, -29))
	await frames(100)
	check(game.extraction_progress > 1 and not game.ended, "Gate 3 is free without fuse or key")
	await place(Vector3(22, 1, -23))
	check(game.extraction_progress == 0, "leaving extraction resets timer")
	await place(Vector3(22, 1, -29))
	await frames(440)
	check(game.ended and not p.raid_active, "continuous extraction ends raid")
	check(FileAccess.file_exists(game.raid_save_path), "extraction persists only carried loot")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(game.raid_save_path))
	# Independent grid and vital-region regressions.
	var bag := RaidBackpack.new()
	check(bag.add("步枪") and bag.add("战术背心"), "backpack places different item footprints")
	check(not bag.fits(0, 0, 1, 1), "backpack rejects overlapping placement")
	var v := RaidVitals.new()
	v.hit(48, "head", 50)
	check(v.dead, "unprotected head hit is fatal")
	v = RaidVitals.new()
	v.hit(70, "left_leg", 50)
	v.heal()
	check(v.hp.left_leg == 0, "medical kit does not resurrect destroyed limbs")
	game.queue_free()
	await frames(2)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	await frames(5)
	game.player.take_damage(150, "thorax", 100)
	check(game.ended and not game.player.raid_active, "fatal vital-region injury terminates raid without respawn")
	print("CLASSIC_FACTORY_TEST_RESULT ", checks, " checks; ", "PASS" if failures.is_empty() else failures)
	quit(0 if failures.is_empty() else 1)


