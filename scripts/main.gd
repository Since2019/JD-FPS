extends Node3D

var player
var factory
var backpack := RaidBackpack.new()
var stash: Array = []
var stash_path := "user://classic_stash.json"
var raid_save_path := "user://last_raid.json"
var ended := false
var deployed := false
var kills := 0
var raid_time := 1200.0
var extraction_progress := 0.0
var active_exit := ""
var search_progress := 0.0
var target_loot := -1
var searching := false
var exit_display := 0.0
var last_o := 0.0
var selected_id := -1
var medical_id := -1
var energy := 100.0
var hydration := 100.0
var preview := false
var test_mode := false
var ui: CanvasLayer
var message_label: Label
var prompt_label: Label
var extraction_label: Label
var status_label: Label
var exits_label: Label
var action_label: Label
var damage_overlay: ColorRect
var stamina_bar: ProgressBar
var arm_bar: ProgressBar
var menu: PanelContainer
var menu_text: Label
var deploy_button: Button
var pack_panel: PanelContainer
var body_label: Label
var equipment_label: Label
var weight_label: Label
var grid: Control
var info_label: Label
var stash_label: Label

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	preview = "--preview" in args
	test_mode = "--test" in args
	factory = preload("res://scripts/classic_factory.gd").new()
	add_child(factory)
	player = preload("res://scripts/tactical_player.gd").new()
	player.position = factory.spawn_position
	player.collision_layer = 2
	player.collision_mask = 1
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.32
	capsule.height = 1.8
	shape.shape = capsule
	player.add_child(shape)
	add_child(player)
	player.died.connect(func(): _finish_raid(false, "阵亡 / KILLED IN ACTION"))
	player.message_requested.connect(show_message)
	player.damage_feedback.connect(_damage_feedback)
	player.inventory_toggled.connect(_toggle_pack)
	player.treatment_finished.connect(_medical_finished)
	player.magazine_dropped.connect(func(rounds: int): _drop_world("弹匣", rounds))
	backpack.add("医疗包")
	backpack.add("绷带")
	_build_ui()
	for pos in factory.enemy_spawns:
		var enemy := TrainingEnemy.new()
		enemy.setup(player, pos)
		enemy.killed.connect(_enemy_killed)
		add_child(enemy)
		if preview: enemy.active = false
		if test_mode: enemy.active = false
	_load_stash()
	player.set_physics_process(false)
	player.set_process_unhandled_input(false)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	for enemy in get_tree().get_nodes_in_group("combat_ai"): enemy.set_physics_process(false)
	if test_mode: deploy()
	if preview:
		deploy()
		player.set_physics_process(false)
		player.set_process_unhandled_input(false)
		player.position = Vector3(17, 1, 28)
		player.rotation.y = 0.25
		if "--office" in args: player.position = Vector3(-6, 7.3, 10)
		if "--tunnel" in args: player.position = Vector3(-22, -2.5, 30); player.rotation.y = -PI / 2
		if "--pack" in args: player.inventory_open = true; _toggle_pack(true)
		await get_tree().create_timer(2).timeout
		get_viewport().get_texture().get_image().save_png("res://classic-%s.png" % ("pack" if "--pack" in args else "office" if "--office" in args else "tunnel" if "--tunnel" in args else "factory"))
		get_tree().quit()

func _load_stash() -> void:
	if not test_mode and FileAccess.file_exists(stash_path):
		var decoded = JSON.parse_string(FileAccess.get_file_as_string(stash_path))
		if decoded is Array: stash = decoded
	stash_label.text = "仓库战利品：%d 件\n%s" % [stash.size(), " / ".join(stash.slice(maxi(0, stash.size() - 7)))]

func deploy() -> void:
	deployed = true
	menu.hide()
	player.set_physics_process(true)
	player.set_process_unhandled_input(true)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	for enemy in get_tree().get_nodes_in_group("combat_ai"): enemy.set_physics_process(true)
	show_message("工厂 / FACTORY    20:00\n双击 O 查看撤离点", 4)

func _label(parent: Node, text: String, pos: Vector2, font_size := 18, color := Color("cecfc3")) -> Label:
	var label := Label.new()
	label.text = text
	label.position = pos
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	label.add_theme_constant_override("shadow_offset_y", 2)
	parent.add_child(label)
	return label

func _panel(pos: Vector2, size: Vector2) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.position = pos
	panel.size = size
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.035, 0.045, 0.04, 0.97)
	style.border_color = Color("686954")
	style.set_border_width_all(1)
	style.set_content_margin_all(24)
	panel.add_theme_stylebox_override("panel", style)
	ui.add_child(panel)
	return panel

func _button(parent: Node, text: String, pos: Vector2, size: Vector2, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.focus_mode = Control.FOCUS_NONE
	button.position = pos
	button.size = size
	button.pressed.connect(callback)
	parent.add_child(button)
	return button

func _build_ui() -> void:
	ui = CanvasLayer.new()
	add_child(ui)
	damage_overlay = ColorRect.new()
	damage_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	damage_overlay.color = Color(0.6, 0, 0, 0)
	damage_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(damage_overlay)
	message_label = _label(ui, "", Vector2(340, 70), 21, Color("d2c69e"))
	message_label.size.x = 600
	message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt_label = _label(ui, "", Vector2(360, 424), 19)
	prompt_label.size.x = 560
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	extraction_label = _label(ui, "", Vector2(390, 510), 24, Color("a2c194"))
	action_label = _label(ui, "", Vector2(510, 566), 18, Color("d6c88d"))
	exits_label = _label(ui, "", Vector2(955, 35), 18, Color("d4d0b9"))
	status_label = _label(ui, "", Vector2(28, 618), 16)
	for i in 2:
		var bar := ProgressBar.new()
		bar.position = Vector2(28, 652 + i * 13)
		bar.size = Vector2(170, 7)
		bar.show_percentage = false
		var background := StyleBoxFlat.new()
		background.bg_color = Color(0.1, 0.12, 0.1, 0.7)
		var fill := StyleBoxFlat.new()
		fill.bg_color = Color("a8b6a1") if i == 0 else Color("bfb38e")
		bar.add_theme_stylebox_override("background", background)
		bar.add_theme_stylebox_override("fill", fill)
		bar.modulate = Color("a8b6a1") if i == 0 else Color("bfb38e")
		ui.add_child(bar)
		if i == 0: stamina_bar = bar
		else: arm_bar = bar
	_label(ui, "1  АК-74Н     4  医疗     G  手雷     TAB  装备", Vector2(770, 672), 15, Color("999b89"))
	pack_panel = _panel(Vector2(120, 90), Vector2(1040, 550))
	var content := Control.new()
	content.custom_minimum_size = Vector2(990, 500)
	pack_panel.add_child(content)
	_label(content, "装备  /  健康", Vector2(0, 0), 24)
	body_label = _label(content, "", Vector2(0, 54), 18)
	equipment_label = _label(content, "", Vector2(240, 54), 17)
	weight_label = _label(content, "", Vector2(530, 10), 19)
	grid = Control.new()
	grid.position = Vector2(530, 54)
	grid.size = Vector2(408, 340)
	content.add_child(grid)
	info_label = _label(content, "点击物品后：使用 / 丢弃 / 旋转", Vector2(530, 407), 16)
	_button(content, "使用", Vector2(530, 442), Vector2(90, 38), _use_selected)
	_button(content, "丢弃", Vector2(630, 442), Vector2(90, 38), _drop_selected)
	_button(content, "旋转", Vector2(730, 442), Vector2(90, 38), func(): backpack.rotate_item(selected_id); _refresh_grid())
	_button(content, "返回", Vector2(840, 442), Vector2(90, 38), func(): player.inventory_open = false; _toggle_pack(false))
	_label(content, "R 换弹 · 双击 R 快速换弹\nAlt+R 检查弹匣 · Alt+T 检查膛内\nB 切换快慢机 · P 为备用弹匣压弹\n滚轮调步速 · C 蹲伏 · X 匍匐\nQ/E 侧倾 · Alt 屏息 · T 手电\n打开背包时战局继续", Vector2(0, 318), 16)
	pack_panel.hide()
	menu = _panel(Vector2(340, 165), Vector2(600, 390))
	var menu_content := VBoxContainer.new()
	menu_content.add_theme_constant_override("separation", 18)
	menu.add_child(menu_content)
	menu_text = Label.new()
	menu_text.text = "工厂 / FACTORY\n经典布局 · 离线突袭\n\nAK-74N · 3 个备用弹匣 · 医疗包 · 2 枚手雷\n搜刮后抵达撤离点，带出物资进入仓库。"
	menu_text.add_theme_font_size_override("font_size", 20)
	menu_content.add_child(menu_text)
	stash_label = Label.new()
	stash_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stash_label.custom_minimum_size = Vector2(510, 50)
	menu_content.add_child(stash_label)
	deploy_button = Button.new()
	deploy_button.text = "进入工厂"
	deploy_button.focus_mode = Control.FOCUS_NONE
	deploy_button.custom_minimum_size.y = 48
	deploy_button.pressed.connect(func():
		if ended: get_tree().reload_current_scene()
		else: deploy()
	)
	menu_content.add_child(deploy_button)

func _unhandled_input(event: InputEvent) -> void:
	if ended or not deployed: return
	if event is InputEventKey and event.pressed and not event.echo:
		var key: int = event.physical_keycode if event.physical_keycode != 0 else event.keycode
		if key == KEY_O:
			var now := Time.get_ticks_msec() / 1000.0
			exit_display = 8.0 if now - last_o < 0.4 else 3.0
			last_o = now
		if key in [KEY_H, KEY_4] and medical_id < 0:
			selected_id = backpack.find_item("医疗包")
			_use_selected()
		if key == KEY_ESCAPE and player.action_kind == "pack": player.cancel_action()

func _process(delta: float) -> void:
	if not deployed or ended or preview: return
	raid_time = maxf(0, raid_time - delta)
	if raid_time <= 0: _finish_raid(false, "行动超时 / MISSING IN ACTION"); return
	energy = maxf(0, energy - delta * (0.028 if player.sprinting else 0.01))
	hydration = maxf(0, hydration - delta * 0.018)
	player.carry_weight = 23 + backpack.weight() + (player.loose_rounds / 100.0)
	if energy <= 0 or hydration <= 0: player.vitals.hit(delta * 0.5, "thorax", 100)
	stamina_bar.value = player.stamina
	arm_bar.value = player.arm_stamina
	status_label.text = "%s  %d%%\n%s" % [["站立", "蹲伏", "匍匐"][player.stance], int(player.walk_fraction * 100), "失血" if player.bleeding else ("腿部受伤" if player.vitals.leg_injured() else "")]
	var action_names := {"reload": "更换弹匣", "check_mag": "检查弹匣", "check_chamber": "检查膛内", "pack": "逐发压弹", "medical": "治疗", "bandage": "包扎止血", "grenade": "准备投掷"}
	action_label.text = "%s  %.1fs" % [action_names.get(player.action_kind, ""), maxf(0, player.action_left)] if player.action_kind != "" else ""
	exit_display = maxf(0, exit_display - delta)
	exits_label.text = "剩余时间  %02d:%02d\n\nGate 3      可用\nGate 0      需要工厂钥匙\nCellars      需要工厂钥匙" % [int(raid_time) / 60, int(raid_time) % 60] if exit_display > 0 else ""
	if player.inventory_open:
		player.interacting = false
		_refresh_pack_text()
		search_progress = 0
		prompt_label.text = ""
	else: _interaction(delta)
	_update_extraction(delta)

func _visible_interaction(at: Vector3, allowed: Node = null) -> bool:
	if player.camera.global_position.distance_to(at) > 2.6: return false
	if (at - player.camera.global_position).normalized().dot(-player.camera.global_basis.z) < 0.7: return false
	var query := PhysicsRayQueryParameters3D.create(player.camera.global_position, at)
	query.collision_mask = 1
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.collider == allowed or hit.position.distance_to(at) < 0.02

func _interaction(delta: float) -> void:
	prompt_label.text = ""
	searching = false
	player.interacting = false
	if player.action_kind != "" or player.sprinting:
		search_progress = 0
		return
	for door in factory.doors:
		if _visible_interaction(door.target_position(), door.leaf):
			prompt_label.text = "F  %s  %s" % ["关闭" if door.opened else ("解锁" if door.locked else "打开"), door.title]
			if Input.is_action_just_pressed("interact"):
				if not door.interact(backpack.has("工厂紧急出口钥匙")): show_message("需要工厂紧急出口钥匙", 2)
				else: player.gunshot_heard.emit(door.global_position, 8)
			search_progress = 0
			return
	var previous := target_loot
	target_loot = -1
	for i in factory.loot.size():
		var entry: Dictionary = factory.loot[i]
		if not entry.taken and _visible_interaction(entry.position, entry.get("node")): target_loot = i; break
	if previous != target_loot: search_progress = 0
	if target_loot < 0: search_progress = 0; return
	var entry: Dictionary = factory.loot[target_loot]
	var duration: float = entry.get("duration", 2.6)
	prompt_label.text = "按住 F  搜索%s  %.1f / %.1f" % [entry.title, search_progress, duration]
	if Input.is_action_pressed("interact") and player.velocity.length() < 0.35:
		searching = true
		player.interacting = true
		search_progress += delta
		if search_progress >= duration:
			if backpack.add(entry.item, entry.get("rounds", -1)):
				entry.taken = true
				show_message("已收取：" + entry.item, 2)
			else: show_message("背包空间不足", 2)
			search_progress = 0
	else: search_progress = 0

func _update_extraction(delta: float) -> void:
	var found := ""
	for entry in factory.exits:
		var flat := Vector2(player.position.x - entry.position.x, player.position.z - entry.position.z).length()
		if flat > entry.radius or absf(player.position.y - 0.9 - entry.position.y) > 0.8: continue
		if entry.key and not backpack.has("工厂紧急出口钥匙"):
			extraction_label.text = "需要工厂紧急出口钥匙"
			extraction_progress = 0
			return
		found = entry.name
		break
	if found == "":
		active_exit = ""
		extraction_progress = 0
		extraction_label.text = ""
		return
	if active_exit != found: extraction_progress = 0
	active_exit = found
	extraction_progress += delta
	extraction_label.text = "%s  撤离中  %.1f" % [found, maxf(0, 7 - extraction_progress)]
	if extraction_progress >= 7: _finish_raid(true, "成功撤离 / SURVIVED")

func _toggle_pack(open: bool) -> void:
	pack_panel.visible = open
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if open else Input.MOUSE_MODE_CAPTURED
	if open: _refresh_grid(); _refresh_pack_text()

func _refresh_pack_text() -> void:
	body_label.text = player.vitals.description() + "\n\n能量  %d   水分  %d" % [energy, hydration]
	equipment_label.text = "AK-74N / 5.45 × 39\n护甲耐久  %d / 50\n\n已装弹匣  %d\n膛内  %s\n备用弹匣  %s\n散弹  %d\n手雷  %d\n\nP 逐发装填备用弹匣" % [player.vitals.armor, player.ammo, "有弹" if player.chambered else "空", str(player.magazines), player.loose_rounds, player.grenade_count]
	weight_label.text = "背包  6 × 5     负重 %.1f kg" % player.carry_weight

func _refresh_grid() -> void:
	for child in grid.get_children(): grid.remove_child(child); child.queue_free()
	for y in 5:
		for x in 6:
			var cell := ColorRect.new()
			cell.position = Vector2(x * 66, y * 66)
			cell.size = Vector2(64, 64)
			cell.color = Color("2c322c")
			grid.add_child(cell)
	for entry in backpack.entries:
		var button := _button(grid, entry.name + ("\n%d 发" % entry.rounds if entry.rounds >= 0 else ""), Vector2(entry.x * 66, entry.y * 66), Vector2(entry.w * 66 - 2, entry.h * 66 - 2), func(): selected_id = entry.id; info_label.text = "%s · %.1f kg" % [entry.name, entry.weight])
		button.add_theme_font_size_override("font_size", 14)

func _use_selected() -> void:
	for entry in backpack.entries:
		if entry.id != selected_id: continue
		if entry.name in ["医疗包", "绷带"]:
			if player.vitals.total() >= 440 and not player.bleeding: return
			if player.begin_action("bandage" if entry.name == "绷带" else "medical", 4.0):
				medical_id = entry.id
				player.inventory_open = false
				_toggle_pack(false)
		elif entry.name == "饮用水": hydration = minf(100, hydration + 60); backpack.remove(entry.id); _refresh_grid()
		elif entry.name == "步枪弹药": player.add_ammo(30); backpack.remove(entry.id); _refresh_grid()
		elif entry.name == "弹匣" and player.magazines.size() < 5:
			player.magazines.append(maxi(0, entry.rounds)); backpack.remove(entry.id); _refresh_grid()
		return

func _medical_finished() -> void:
	backpack.remove(medical_id)
	medical_id = -1
	_refresh_grid()

func _drop_selected() -> void:
	if selected_id == medical_id: return
	var item := backpack.remove(selected_id)
	if not item.is_empty(): _drop_world(item.name, item.rounds)
	selected_id = -1
	_refresh_grid()

func _drop_world(item: String, rounds := -1) -> void:
	var p: Vector3 = player.position - player.global_basis.z * 0.75
	var obstruction := PhysicsRayQueryParameters3D.create(player.camera.global_position, p)
	obstruction.collision_mask = 1
	var wall := get_world_3d().direct_space_state.intersect_ray(obstruction)
	if wall: p = wall.position + wall.normal * 0.5
	var floor_query := PhysicsRayQueryParameters3D.create(p + Vector3.UP * 0.2, p - Vector3.UP * 3)
	floor_query.collision_mask = 1
	var floor_hit := get_world_3d().direct_space_state.intersect_ray(floor_query)
	p.y = floor_hit.position.y + 0.32 if floor_hit else player.position.y - 0.55
	factory._loot_box(p, "掉落物", item, "green")
	factory.loot.back().rounds = rounds
	factory.loot.back().duration = 0.6

func _enemy_killed(enemy: TrainingEnemy) -> void:
	kills += 1
	factory.loot.append({"position": enemy.position + Vector3.UP * 0.45, "title": "尸体", "item": "战术背心", "taken": false, "duration": 4.0})
	factory.loot.append({"position": enemy.position + Vector3(0.2, 0.35, 0.2), "title": "尸体武器", "item": "步枪", "taken": false, "duration": 2.5})

func _finish_raid(success: bool, reason: String) -> void:
	if ended: return
	ended = true
	player.raid_active = false
	player.set_physics_process(false)
	player.set_process_unhandled_input(false)
	player.cancel_action()
	for enemy in get_tree().get_nodes_in_group("combat_ai"):
		enemy.active = false
		enemy.set_physics_process(false)
	for child in get_children():
		if child.get_script() in [preload("res://scripts/bullet.gd"), preload("res://scripts/grenade.gd")]: child.queue_free()
	pack_panel.hide()
	menu.show()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	menu_text.text = "%s\n\n击杀 %d · 行动 %d 秒\n%s" % [reason, kills, int(1200 - raid_time), "带出物资 %d 件" % backpack.entries.size() if success else "随身装备及战利品遗失"]
	deploy_button.text = "返回部署"
	prompt_label.text = ""
	if success:
		stash.append_array(backpack.names())
		var file := FileAccess.open(raid_save_path, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify({"loot": backpack.names(), "kills": kills, "seconds": int(1200 - raid_time), "exit": active_exit}))
		if not test_mode:
			var storage := FileAccess.open(stash_path, FileAccess.WRITE)
			if storage: storage.store_string(JSON.stringify(stash))
	stash_label.text = "仓库战利品：%d 件" % stash.size()

func _damage_feedback(amount: float) -> void:
	damage_overlay.color = Color(0.45, 0, 0, clampf(amount / 100, 0.1, 0.45))
	create_tween().tween_property(damage_overlay, "color:a", 0, 0.7)

func show_message(text: String, duration: float = 1.0) -> void:
	if not message_label: return
	message_label.text = text
	get_tree().create_timer(duration).timeout.connect(func():
		if is_instance_valid(message_label) and message_label.text == text: message_label.text = ""
	)
