extends "res://scripts/factory.gd"

# Classic Factory topology reconstructed from the public Johnny Tushonka map.
# Coordinates and prop dimensions are estimated; this is not an original game map export.
var doors: Array[Node3D] = []
var tunnel_rects: Array[Rect2] = []
var exits: Array[Dictionary] = []
var spawn_position := Vector3(-28, 1, -25)
var enemy_spawns := [Vector3(13, 0, -22), Vector3(15, 0, 12), Vector3(-21, 0, 8), Vector3(-5, 6.5, 2), Vector3(12, -3.4, 28), Vector3(-25, 0, -8)]

func _ready() -> void:
	_material("wall", Color("8b8774"), false, true)
	_material("floor", Color("827d69"), false, true)
	_material("steel", Color("424b49"), true)
	_material("rust", Color("866346"), true)
	_material("green", Color("536953"), true)
	_material("yellow", Color("b8984e"), true)
	_material("dark", Color("242d2a"), true)
	_material("paper", Color("b9b4a0"))
	_material("red", Color("814232"), true)
	_material("blue", Color("4e7783"), true)
	_floors_and_shell()
	_classic_halls()
	_classic_office()
	_tunnels()
	_classic_exits()
	_seal_tunnels()
	_classic_lights()
	_classic_loot()
	_build_navigation()

func _build_navigation() -> void:
	var mesh := NavigationMesh.new()
	mesh.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	mesh.geometry_collision_mask = 1
	mesh.agent_radius = 0.4
	mesh.agent_height = 1.9
	mesh.agent_max_climb = 0.3
	mesh.agent_max_slope = 40
	mesh.cell_size = 0.2
	mesh.cell_height = 0.1
	# Doors are operated by actors; omit leaves from the static navigation bake.
	for door in doors: door.leaf.collision_layer = 8
	var source := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(mesh, source, self)
	for door in doors: door.leaf.collision_layer = 1
	NavigationServer3D.bake_from_source_geometry_data(mesh, source)
	var region := NavigationRegion3D.new()
	region.navigation_mesh = mesh
	add_child(region)

func _floors_and_shell() -> void:
	# Omit tiles at actual basement stairwells instead of covering them with a slab.
	for x in range(-36, 28, 4):
		for z in range(-32, 32, 4):
			if (x == -28 or x == 16) and z >= 20: continue
			if x == -24 and z >= -24 and z < -12: continue
			_box("车间地坪", Vector3(4, 0.3, 4), Vector3(x + 2, -0.15, z + 2), "floor")
	for x in [-36, 28]:
		_box("外墙", Vector3(0.4, 11, 64), Vector3(x, 5.5, 0), "wall")
		_box("绿墙裙", Vector3(0.42, 2.5, 64), Vector3(x, 1.25, 0), "green", false)
	for z in [-32, 32]:
		_box("外墙", Vector3(64, 11, 0.4), Vector3(-4, 5.5, z), "wall")
	_box("屋顶", Vector3(64, 0.25, 64), Vector3(-4, 11, 0), "dark")
	# Extraction corridors remain inside the perimeter to keep the playable shell sealed.
	for z in [-24, -8, 8, 24]:
		_box("屋架", Vector3(64, 0.45, 0.45), Vector3(-4, 9.8, z), "steel")
		for x in [-30, -14, 10, 24]:
			_box("工字钢柱", Vector3(0.35, 10, 0.5), Vector3(x, 5, z), "steel")
			for y in [0.5, 1, 1.5]: _box("柱脚警戒色", Vector3(0.37, 0.18, 0.52), Vector3(x, y, z), "yellow", false)
	for x in [-18, -17.3, 11]:
		_cylinder(Vector3(x, 7.7, 0), 0.18, 60, "rust", Vector3(90, 0, 0), false)

func _classic_halls() -> void:
	# The large hall, tank hall and long eastern forklift hall are connected by choke points.
	_box("罐区北隔墙", Vector3(15, 5.6, 0.3), Vector3(-28.5, 2.8, -12), "wall")
	_box("罐区北隔墙", Vector3(7, 5.6, 0.3), Vector3(-12.5, 2.8, -12), "wall")
	_box("东车间隔墙", Vector3(0.3, 5.6, 10), Vector3(4, 2.8, -25), "wall")
	_box("东车间隔墙", Vector3(0.3, 5.6, 15), Vector3(4, 2.8, 22.5), "wall")
	for p in [Vector3(-28, 0, -4), Vector3(-20, 0, -4), Vector3(-28, 0, 8), Vector3(-20, 0, 8)]:
		_cylinder(p + Vector3.UP * 2.1, 2.15, 4.2, "green")
		for y in [0.3, 3.9]: _cylinder(p + Vector3.UP * y, 2.2, 0.14, "steel")
		_cylinder(p + Vector3.UP * 4.8, 0.25, 1.3, "rust")
		_box("储罐基座", Vector3(4.7, 0.22, 4.7), p + Vector3.UP * 0.11, "dark")
		_sign("ОПАСНО", p + Vector3(0, 2, 2.16), 0, 22)
	for p in [Vector3(-10, 0, -26), Vector3(14, 0, -14), Vector3(18, 0, 7), Vector3(11, 0, 22)]:
		_container(p)
	# Forklift silhouette with forks, mast, cab and tires, all at human scale.
	var fp := Vector3(19, 0, 18)
	_box("叉车底盘", Vector3(1.6, 0.7, 2.4), fp + Vector3.UP * 0.65, "yellow")
	_box("叉车后配重", Vector3(1.6, 1.1, 0.7), fp + Vector3(0, 1.1, 0.9), "yellow")
	for x in [-0.65, 0.65]:
		_box("叉车门架", Vector3(0.15, 3, 0.2), fp + Vector3(x, 1.5, -1.2), "steel")
		_box("叉车货叉", Vector3(0.15, 0.1, 1.8), fp + Vector3(x, 0.2, -2), "steel")
		for z in [-0.7, 0.7]: _cylinder(fp + Vector3(x * 1.25, 0.45, z), 0.43, 0.25, "dark", Vector3(0, 0, 90))
	for x in [-0.7, 0.7]: _box("驾驶室框", Vector3(0.1, 1.8, 0.1), fp + Vector3(x, 1.5, 0.4), "steel")
	_box("叉车顶棚", Vector3(1.6, 0.1, 1.5), fp + Vector3.UP * 2.5, "dark")
	# Small pumping station with a real door.
	_box("泵房北墙", Vector3(7, 3, 0.2), Vector3(11.5, 1.5, 0), "wall")
	_box("泵房东墙", Vector3(0.2, 3, 6), Vector3(15, 1.5, 3), "wall")
	_box("泵房西墙", Vector3(0.2, 3, 6), Vector3(8, 1.5, 3), "wall")
	_doorway(Vector3(11.5, 0, 6), 7, "泵房", false)
	for z in [1.5, 4]: _cylinder(Vector3(11, 0.7, z), 0.5, 1.4, "blue", Vector3(0, 0, 90))
	# Safe insertion pockets and close-range cover.
	_box("出生区遮挡", Vector3(6, 3, 0.2), Vector3(-29, 1.5, -20), "wall")
	for p in [Vector3(-16, 0, 18), Vector3(22, 0, -5), Vector3(-30, 0, -27), Vector3(8, 0, -25)]:
		_box("木箱掩体", Vector3(2.2, 1.3, 1.5), p + Vector3.UP * 0.65, "rust")
		for x in [-0.9, 0.9]: _box("打包钢带", Vector3(0.07, 1.32, 1.52), p + Vector3(x, 0.66, 0), "steel", false)
	for z in range(-26, 26, 4):
		_box("车道边线", Vector3(0.08, 0.01, 2.7), Vector3(6, 0.01, z), "yellow", false)
	_sign("ЦЕХ 01", Vector3(-18, 7, -31.7), 0, 60)
	_sign("ЦЕХ 02", Vector3(-35.7, 6, 3), 90, 60)

func _container(p: Vector3) -> void:
	_box("蓝色货箱", Vector3(2.5, 2.6, 5.8), p + Vector3.UP * 1.3, "blue")
	for z in range(-13, 14):
		for x in [-1.27, 1.27]: _box("波纹钢板", Vector3(0.06, 2.55, 0.05), p + Vector3(x, 1.3, z * 0.21), "steel", false)

func _classic_office() -> void:
	# Three storeys: ground corridor, showers/lockers, upper office/safe room.
	for level in [0, 1, 2]:
		var y: float = level * 3.2
		if level > 0: _box("办公室楼板", Vector3(10, 0.2, 24), Vector3(-3, y - 0.1, 0), "floor")
		_box("办公室东墙", Vector3(0.2, 3.2, 24), Vector3(2, y + 1.6, 0), "wall")
		for z in [-12, 12]: _box("办公室端墙", Vector3(10, 3.2, 0.2), Vector3(-3, y + 1.6, z), "wall")
		# West facade has openings opposite each landing.
		for segment in [[-12.0, -3.2], [-0.8, 8.8], [11.2, 12.0]]:
			_box("办公室西墙", Vector3(0.2, 3.2, segment[1] - segment[0]), Vector3(-8, y + 1.6, (segment[0] + segment[1]) / 2), "wall")
		for z in [-2, 10]: _box("西门门梁", Vector3(0.2, 0.7, 2.4), Vector3(-8, y + 2.85, z), "wall")
		# Corridor separated from rooms, with door openings.
		for segment in [[-12.0, -8.0], [-6.5, 0.0], [1.5, 12.0]]:
			_box("走廊隔墙", Vector3(0.18, 3, segment[1] - segment[0]), Vector3(-4, y + 1.5, (segment[0] + segment[1]) / 2), "green")
		for z in [-7.25, 0.75]:
			var door := _add_door(Vector3(-4, y, z + 0.75), "办公室门" if level == 2 else "更衣室门", false)
			door.rotation_degrees.y = 90
		_box("房间隔墙", Vector3(6, 3, 0.18), Vector3(-1, y + 1.5, -3), "wall")
		_lamp(Vector3(-6, y + 2.8, -7), Color("d3d2ab"), 0.8, 8)
		_lamp(Vector3(-6, y + 2.8, 7), Color("d3d2ab"), 0.8, 8)
		_sign("ЭТАЖ %d" % (level + 1), Vector3(-7.85, y + 2.2, 6), 90, 24)
		if level == 1:
			for z in [3, 4.5, 6, 7.5, 9]:
				_box("更衣柜", Vector3(0.7, 2.1, 1.2), Vector3(1.3, y + 1.05, z), "blue")
			for z in [-10, -8, -6]:
				_box("淋浴隔板", Vector3(2, 2, 0.12), Vector3(0, y + 1, z), "paper")
		if level == 2:
			for z in [-9, 4, 8]:
				_box("办公桌", Vector3(2.4, 0.15, 1.1), Vector3(0, y + 0.85, z), "rust")
				for x in [-1, 1]: _box("桌腿", Vector3(0.08, 0.8, 1), Vector3(x, y + 0.4, z), "steel")
			_box("办公室保险柜", Vector3(0.8, 1.2, 0.65), Vector3(0.9, y + 0.6, -10.9), "dark")
	_box("办公室屋顶", Vector3(10, 0.2, 24), Vector3(-3, 9.6, 0), "dark")
	_stair(Vector3(-11, 0, 22), Vector3(-11, 3.2, 10), 2.6)
	_stair(Vector3(-11, 3.2, 10), Vector3(-11, 6.4, -2), 2.6)
	_rail(Vector3(-12.3, 6.4, -2.2), Vector3(-9.7, 6.4, -2.2))
	for pair in [[3.2, 10.0], [6.4, -2.0]]:
		_box("楼梯平台", Vector3(1.8, 0.18, 2.4), Vector3(-8.8, pair[0] - 0.09, pair[1]), "steel")
	_box("罐区高架猫道", Vector3(15, 0.18, 2.2), Vector3(-19.5, 6.31, -2), "steel")
	for z in [-3.1, -0.9]: _rail(Vector3(-27, 6.4, z), Vector3(-12, 6.4, z))
	_box("北侧猫道", Vector3(2.2, 0.18, 23), Vector3(-27, 6.31, -14.5), "steel")
	for x in [-28.1, -25.9]: _rail(Vector3(x, 6.4, -26), Vector3(x, 6.4, -3.1))

func _stair(a: Vector3, b: Vector3, width: float) -> void:
	var length := a.distance_to(b)
	var ramp := _box("连续楼梯碰撞", Vector3(width, 0.16, length + 0.3), (a + b) / 2 - Vector3.UP * 0.08, "steel")
	ramp.look_at(b - Vector3.UP * 0.08)
	var count := int(length / 0.42)
	for i in count:
		var p := a.lerp(b, float(i) / count)
		_box("楼梯踏步", Vector3(width, 0.04, 0.4), p + Vector3.UP * 0.015, "steel", false)
	for x in [-width * 0.5, width * 0.5]: _rail(a.lerp(b, 0.1) + Vector3(x, 0, 0), b.lerp(a, 0.1) + Vector3(x, 0, 0))

func _tunnels() -> void:
	# Two southern ramps join an underground loop; a third connects the northern hall.
	_stair(Vector3(-26, 0, 20), Vector3(-26, -3.4, 30), 3.8)
	_stair(Vector3(18, 0, 20), Vector3(18, -3.4, 30), 3.8)
	_stair(Vector3(-22, 0, -24), Vector3(-22, -3.4, -14), 3.8)
	_tunnel_x(-26, 18, 30)
	_tunnel_z(-26, -6, 30)
	_tunnel_x(-26, -16, -6)
	_tunnel_z(-16, -14, 30)
	_tunnel_x(-22, -16, -14)
	_tunnel_z(18, 20, 30)
	_tunnel_z(-22, -24, -14)
	for p in [Vector3(-26, -0.8, 24), Vector3(-26, -0.8, 8), Vector3(-18, -0.8, -10), Vector3(-8, -0.8, 30), Vector3(17, -0.8, 30)]:
		_lamp(p, Color("d5a475"), 0.65, 8)
	_sign("ПОДВАЛ", Vector3(-26, 1.4, 18.5), 0, 28)

func _tunnel_x(a: float, b: float, z: float) -> void:
	_box("地下地板", Vector3(b - a + 4, 0.2, 4), Vector3((a + b) / 2, -3.5, z), "floor")
	tunnel_rects.append(Rect2(a - 2, z - 2, b - a + 4, 4))

func _tunnel_z(x: float, a: float, b: float) -> void:
	_box("地下地板", Vector3(4, 0.2, b - a + 4), Vector3(x, -3.5, (a + b) / 2), "floor")
	tunnel_rects.append(Rect2(x - 2, a - 2, 4, b - a + 4))

func _seal_tunnels() -> void:
	# Build the boundary of the union, leaving only actual corridor junctions open.
	var occupied := {}
	for rect in tunnel_rects:
		for x in range(int(rect.position.x), int(rect.end.x), 2):
			for z in range(int(rect.position.y), int(rect.end.y), 2): occupied[Vector2i(x, z)] = true
	for cell: Vector2i in occupied:
		for offset in [Vector2i(2, 0), Vector2i(-2, 0), Vector2i(0, 2), Vector2i(0, -2)]:
			if occupied.has(cell + offset): continue
			var p := Vector3(cell.x + 1 + offset.x * 0.5, -1.85, cell.y + 1 + offset.y * 0.5)
			_box("地下闭合边墙", Vector3(0.15, 3.1, 2) if offset.x != 0 else Vector3(2, 3.1, 0.15), p, "wall")

func _add_door(pos: Vector3, title: String, locked: bool) -> Node3D:
	var door := preload("res://scripts/door.gd").new()
	door.position = pos
	door.title = title
	door.locked = locked
	add_child(door)
	doors.append(door)
	return door

func _doorway(pos: Vector3, width: float, title: String, locked: bool) -> void:
	for side in [-1, 1]:
		_box("门侧墙", Vector3((width - 1.5) / 2, 3, 0.18), pos + Vector3(side * (width + 1.5) / 4, 1.5, 0), "wall")
	_box("门框", Vector3(1.5, 0.55, 0.2), pos + Vector3.UP * 2.725, "wall")
	_add_door(pos + Vector3.LEFT * 0.75, title, locked)

func _classic_exits() -> void:
	exit_position = Vector3(22, 0, -29)
	for x in [19, 25]: _box("Gate3通道侧墙", Vector3(0.2, 3.2, 12), Vector3(x, 1.6, -26), "wall")
	_doorway(Vector3(22, 0, -21), 6, "Gate 3 外门", false)
	_doorway(Vector3(22, 0, -26), 6, "Gate 3 内门", false)
	_sign("ВЫХОД  3", Vector3(22, 2.5, -31.7), 0, 32)
	exits.append({"name": "Gate 3", "position": exit_position, "key": false, "radius": 1.8})
	# Gate 0 pocket in the opposite end of the northern hall.
	_box("Gate0侧墙", Vector3(0.2, 3, 7), Vector3(-31, 1.5, -28.5), "wall")
	_doorway(Vector3(-33.5, 0, -25), 5, "Gate 0", true)
	_sign("ВЫХОД  0", Vector3(-33.5, 2.4, -31.7), 0, 30)
	exits.append({"name": "Gate 0", "position": Vector3(-33.5, 0, -29), "key": true, "radius": 1.7})
	_tunnel_x(-32, -26, -6)
	for z in [-8, -4]: _box("Cellars侧墙", Vector3(8, 2.8, 0.18), Vector3(-29, -2, z), "wall")
	var door := _add_door(Vector3(-29, -3.4, -5.25), "Cellars", true)
	door.rotation_degrees.y = 90
	for z in [-7.375, -4.625]: _box("Cellars门侧墙", Vector3(0.2, 2.8, 1.25), Vector3(-29, -2, z), "wall")
	_box("Cellars端墙", Vector3(0.2, 2.8, 4), Vector3(-34, -2, -6), "wall")
	_sign("ВЫХОД", Vector3(-33.8, -1.2, -6), 90, 28)
	exits.append({"name": "Cellars", "position": Vector3(-32, -3.4, -6), "key": true, "radius": 1.5})
	for entry in exits: _lamp(entry.position + Vector3.UP * 2.5, Color("92c390"), 0.45, 4)

func _classic_lights() -> void:
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("171d1a")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("b4b9ae")
	env.ambient_light_energy = 0.45
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = env
	add_child(world)
	for p in [Vector3(-24, 9.5, -22), Vector3(-22, 9.5, 4), Vector3(17, 9.5, -15), Vector3(17, 9.5, 12)]:
		var light := SpotLight3D.new()
		light.position = p
		light.rotation_degrees.x = -90
		light.spot_range = 28
		light.spot_angle = 65
		light.light_energy = 4
		light.light_color = Color("d5dcc9")
		light.shadow_enabled = true
		add_child(light)
		_lamp(p - Vector3.UP, Color("e6c79d"), 2.2, 16)
		for x in [-2.5, 0, 2.5]:
			var pane := _box("屋顶天窗", Vector3(2.3, 0.08, 4), p + Vector3(x, 1.2, 0), "paper", false)
			var mat := StandardMaterial3D.new()
			mat.albedo_color = Color("c9d4ce")
			mat.emission_enabled = true
			mat.emission = Color("859b94")
			pane.get_child(0).material_override = mat

func _classic_loot() -> void:
	_loot_box(Vector3(-28, 0.65, -28), "运动包", "绷带", "green")
	_loot_box(Vector3(-16, 0.65, -25), "工具箱", "机械零件", "red")
	_loot_box(Vector3(0, 7.05, -10), "保险柜", "情报文件", "dark")
	_loot_box(Vector3(0.8, 4.0, 7), "夹克", "工厂紧急出口钥匙", "green")
	_loot_box(Vector3(9, 0.65, -24), "武器箱", "步枪弹药", "green")
	_loot_box(Vector3(13, 0.65, 3), "工具箱", "电钻", "blue")
	_loot_box(Vector3(-24, -2.75, 30), "医疗包", "医疗包", "green")
	_loot_box(Vector3(23, 0.65, 13), "物资箱", "饮用水", "rust")
