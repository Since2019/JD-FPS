extends Node3D

# Original industrial layout, metres. Doors and aisles are actual traversable space.
const CONCRETE = preload("res://assets/textures/weathered_concrete.png")
var materials: Dictionary = {}
var loot: Array[Dictionary] = []
var fuse_panel := Vector3(-20, 1.2, -17)
var exit_position := Vector3(20, 0, -23)

func _ready() -> void:
	_material("wall", Color("77776a"), false, true)
	_material("floor", Color("737367"), false, true)
	_material("steel", Color("353e40"), true)
	_material("rust", Color("70503b"), true)
	_material("green", Color("46584d"), true)
	_material("yellow", Color("ba923b"), true)
	_material("dark", Color("20292c"), true)
	_material("paper", Color("b9b4a0"))
	_material("red", Color("7f392d"), true)
	_shell()
	_structure()
	_machines()
	_offices()
	_details()
	_lighting()
	_loot_box(Vector3(-20, 0.65, 17), "医疗箱", "医疗包", "green")
	_loot_box(Vector3(-18, 0.65, -12), "工具箱", "保险丝", "red")
	_loot_box(Vector3(17, 4.85, -9), "档案箱", "生产档案", "paper")
	_loot_box(Vector3(3, 0.65, -17), "补给箱", "步枪弹药", "green")
	_loot_box(Vector3(8, 0.65, 4), "零件箱", "机械零件", "rust")
	_box("配电柜", Vector3(0.4, 2.0, 1.3), fuse_panel, "green")
	_sign("POWER / 配电室", Vector3(-19.7, 2.8, -17), 90, 28)
	_sign("03  /  EXTRACTION", Vector3(20, 3.8, -23.7), 0, 40)
	_box("撤离门", Vector3(5, 3.5, 0.18), Vector3(20, 1.75, -23.7), "green")
	_lamp(Vector3(20, 3.4, -22.8), Color("82ceab"), 1.5, 5)

func _material(key: String, color: Color, metal := false, texture := false) -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.86
	mat.metallic = 0.55 if metal else 0.0
	if metal:
		var noise := FastNoiseLite.new()
		noise.frequency = 0.06
		var tex := NoiseTexture2D.new()
		tex.width = 256
		tex.height = 256
		tex.noise = noise
		var gradient := Gradient.new()
		gradient.set_color(0, Color(0.38, 0.36, 0.32))
		gradient.set_color(1, Color(0.9, 0.9, 0.85))
		tex.color_ramp = gradient
		mat.albedo_texture = tex
		mat.uv1_triplanar = true
		mat.uv1_scale = Vector3.ONE * 0.8
	if texture:
		mat.albedo_texture = CONCRETE
		mat.uv1_triplanar = true
		mat.uv1_scale = Vector3.ONE * 0.24
	materials[key] = mat

func _box(label: String, size: Vector3, pos: Vector3, material: String, solid := true) -> Node3D:
	var root: Node3D = StaticBody3D.new() if solid else Node3D.new()
	root.name = label
	root.position = pos
	var mesh := MeshInstance3D.new()
	var shape := BoxMesh.new()
	shape.size = size
	mesh.mesh = shape
	mesh.material_override = materials[material]
	root.add_child(mesh)
	if solid:
		var collision := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = size
		collision.shape = box
		root.add_child(collision)
	add_child(root)
	return root

func _cylinder(pos: Vector3, radius: float, height: float, material: String, rotation := Vector3.ZERO, solid := true) -> void:
	var root: Node3D = StaticBody3D.new() if solid else Node3D.new()
	root.position = pos
	root.rotation_degrees = rotation
	var mesh := MeshInstance3D.new()
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = radius
	cylinder.bottom_radius = radius
	cylinder.height = height
	cylinder.radial_segments = 20
	mesh.mesh = cylinder
	mesh.material_override = materials[material]
	root.add_child(mesh)
	if solid:
		var collision := CollisionShape3D.new()
		var shape := CylinderShape3D.new()
		shape.radius = radius
		shape.height = height
		collision.shape = shape
		root.add_child(collision)
	add_child(root)

func _shell() -> void:
	_box("厂房地坪", Vector3(48, 0.5, 50), Vector3(0, -0.25, 0), "floor")
	for x in [-24, 24]:
		_box("砖混侧墙", Vector3(0.5, 10, 50), Vector3(x, 5, 0), "wall")
		_box("旧绿色墙裙", Vector3(0.53, 2.4, 50), Vector3(x, 1.2, 0), "green", false)
	for z in [-25, 25]:
		_box("端墙", Vector3(48, 10, 0.5), Vector3(0, 5, z), "wall")
		_box("旧绿色墙裙", Vector3(48, 2.4, 0.53), Vector3(0, 1.2, z), "green", false)
	_box("厂房屋顶", Vector3(48, 0.25, 50), Vector3(0, 10, 0), "dark")
	# Sheltered insertion room with two routes into the hall.
	_box("入口隔墙", Vector3(14, 3.6, 0.3), Vector3(-17, 1.8, 12), "wall")
	_box("入口隔墙", Vector3(0.3, 3.6, 4), Vector3(-10, 1.8, 23), "wall")
	_sign("01 / RECEIVING", Vector3(-17, 3.1, 12.2), 0, 38)
	_sign("ЗАВОД  /  FACTORY 17", Vector3(0, 7.5, -24.6), 0, 70)

func _structure() -> void:
	for z in [-18, -6, 6, 18]:
		for x in [-11, 11]:
			_box("钢柱", Vector3(0.45, 10, 0.6), Vector3(x, 5, z), "steel")
			_box("柱脚", Vector3(0.85, 0.3, 1), Vector3(x, 0.15, z), "dark")
			for y in [0.5, 1.0, 1.5]:
				_box("柱警戒条", Vector3(0.47, 0.20, 0.62), Vector3(x, y, z), "yellow", false)
		_box("屋架横梁", Vector3(48, 0.5, 0.4), Vector3(0, 9, z), "rust")
		for x in [-18, -6, 6, 18]:
			var brace := _box("桁架斜撑", Vector3(7, 0.16, 0.18), Vector3(x, 8.1, z), "steel", false)
			brace.rotation_degrees.z = 14 if x < 0 else -14
	for x in [-7, -6.3]:
		_cylinder(Vector3(x, 6.6, 0), 0.19, 47, "rust", Vector3(90, 0, 0), false)
	for z in range(-20, 22, 4):
		_box("管道吊架", Vector3(1.5, 0.12, 0.15), Vector3(-6.6, 6.3, z), "steel", false)
	_box("行车吊梁", Vector3(21, 0.8, 0.7), Vector3(0, 7.5, -3), "yellow")
	_box("吊车滑座", Vector3(2, 0.5, 1.6), Vector3(2, 7, -3), "dark")
	_cylinder(Vector3(2, 5.4, -3), 0.035, 3, "steel", Vector3.ZERO, false)
	# Marked lanes connect insertion, workshop, boiler room and exit.
	for x in [-8.8, -4.5]:
		_box("黄色通道线", Vector3(0.09, 0.012, 40), Vector3(x, 0.012, -1), "yellow", false)
	for z in [-21, 10]:
		_box("横向通道线", Vector3(38, 0.012, 0.09), Vector3(0, 0.012, z), "yellow", false)

func _machines() -> void:
	for p in [Vector3(-17, 0, -6), Vector3(-17, 0, 2), Vector3(-17, 0, -18)]:
		_cylinder(p + Vector3.UP * 2.5, 1.8, 5, "green")
		for y in [0.4, 4.5]:
			_cylinder(p + Vector3.UP * y, 1.86, 0.14, "steel")
		_cylinder(p + Vector3(0, 5.6, 0), 0.28, 1.2, "rust")
		_box("锅炉仪表", Vector3(0.55, 0.7, 0.2), p + Vector3(0, 1.5, 1.85), "dark")
		_sign("CAUTION\nPRESSURE", p + Vector3(0, 2.8, 1.83), 0, 22)
	for p in [Vector3(1, 0, 10), Vector3(4, 0, -9), Vector3(5, 0, 1)]:
		_box("机床底座", Vector3(4, 0.5, 2.2), p + Vector3.UP * 0.25, "dark")
		_box("旧铣床", Vector3(1.1, 2.5, 1.5), p + Vector3(-1.3, 1.5, 0), "green")
		_box("工作台", Vector3(3.8, 0.3, 1.7), p + Vector3.UP * 1.1, "steel")
		_cylinder(p + Vector3(0, 1.55, 0), 0.35, 1.8, "rust", Vector3(0, 0, 90))
		_box("控制台", Vector3(0.65, 0.8, 0.4), p + Vector3(-1.3, 1.7, 0.9), "yellow")
	for p in [Vector3(14, 0, 12), Vector3(-2, 0, -16), Vector3(7, 0, 17)]:
		_box("货运箱", Vector3(4, 2.6, 2.6), p + Vector3.UP * 1.3, "rust")
		for x in range(-18, 20, 4):
			_box("货箱加强筋", Vector3(0.06, 2.6, 0.1), p + Vector3(x * 0.1, 1.3, 1.33), "steel", false)
	for p in [Vector3(-3, 0, 4), Vector3(10, 0, -17), Vector3(17, 0, 5)]:
		for x in [0, 0.8]:
			_cylinder(p + Vector3(x, 0.55, 0), 0.36, 1.1, "red")

func _rail(a: Vector3, b: Vector3) -> void:
	var length := a.distance_to(b)
	for y in [0.5, 1.0]:
		var beam := _box("护栏横杆", Vector3(0.065, 0.065, length), (a + b) * 0.5 + Vector3.UP * y, "yellow")
		beam.look_at(b + Vector3.UP * y)
	for i in range(int(length / 1.5) + 1):
		_box("护栏立柱", Vector3(0.07, 1.1, 0.07), a.lerp(b, float(i) / maxf(1, int(length / 1.5))) + Vector3.UP * 0.55, "steel")

func _offices() -> void:
	_box("办公室楼板", Vector3(10, 0.3, 24), Vector3(18, 4.05, -8), "floor")
	_box("办公室外墙", Vector3(0.25, 3, 24), Vector3(23, 5.65, -8), "wall")
	for z in [-20, -12, -4, 4]:
		if z == 4:
			_box("楼梯入口左墙", Vector3(3, 2.8, 0.2), Vector3(14.5, 5.6, z), "wall")
			_box("楼梯入口右墙", Vector3(2, 2.8, 0.2), Vector3(22, 5.6, z), "wall")
			_box("入口门梁", Vector3(5, 0.6, 0.2), Vector3(18.5, 6.7, z), "wall")
		else:
			_box("办公室隔墙", Vector3(6, 2.8, 0.2), Vector3(20, 5.6, z), "wall")
			_box("门上横梁", Vector3(4, 0.6, 0.2), Vector3(15, 6.7, z), "wall")
	for z in [-16, -8, 0]:
		_box("办公桌", Vector3(2.4, 0.16, 1), Vector3(21, 5.0, z), "paper")
		for x in [20, 22]:
			_box("桌腿", Vector3(0.08, 0.8, 0.8), Vector3(x, 4.6, z), "steel")
		_box("档案柜", Vector3(1, 1.9, 0.6), Vector3(22, 5.1, z - 2.5), "green")
		_sign("OFFICE / %02d" % (z + 20), Vector3(20, 6.3, z + 3.85), 180, 25)
	_rail(Vector3(13, 4.2, -17.5), Vector3(13, 4.2, 4))
	for z in [-13, -5, 2]:
		_box("办公室窗下墙", Vector3(0.22, 0.9, 5), Vector3(13, 4.65, z), "green")
		_box("办公室窗梁", Vector3(0.22, 0.5, 5), Vector3(13, 6.75, z), "wall")
		for offset in [-2.5, 0, 2.5]:
			_box("钢窗立框", Vector3(0.12, 2.4, 0.08), Vector3(13, 5.7, z + offset), "steel")
	# Continuous collision ramp under visible steel treads: reliable FPS ascent.
	var ramp := _box("楼梯坡面", Vector3(3.8, 0.2, 12.72), Vector3(18, 2.1, 10), "steel")
	ramp.rotation_degrees.x = 19.29
	for i in range(24):
		_box("钢梯踏板", Vector3(3.8, 0.06, 0.48), Vector3(18, 0.12 + i * 0.175, 15.75 - i * 0.5), "steel", false)
	_rail(Vector3(16, 0.12, 16), Vector3(16, 4.32, 4))
	_rail(Vector3(20, 0.12, 16), Vector3(20, 4.32, 4))
	_box("跨车间猫道", Vector3(26, 0.2, 2.6), Vector3(0, 4.1, -19), "steel")
	_rail(Vector3(-13, 4.2, -20.3), Vector3(13, 4.2, -20.3))
	_rail(Vector3(-13, 4.2, -17.7), Vector3(13, 4.2, -17.7))
	_rail(Vector3(-13, 4.2, -20.3), Vector3(-13, 4.2, -17.7))
	_sign("02 / ADMINISTRATION ↑", Vector3(18, 2.8, 17), 0, 30)

func _details() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1703
	for i in range(95):
		var p := Vector3(rng.randf_range(-22, 22), 0.02, rng.randf_range(-23, 23))
		var paper := _box("碎屑", Vector3(rng.randf_range(0.08, 0.35), 0.015, rng.randf_range(0.15, 0.5)), p, "paper" if i % 3 == 0 else "dark", false)
		paper.rotation.y = rng.randf_range(0, TAU)
	for z in [-10, 0, 10]:
		_box("电缆槽", Vector3(0.16, 0.16, 8), Vector3(-23.6, 3.4, z), "dark", false)
	_sign("BOILER ROOM ←", Vector3(-11, 3.4, 6.4), 0, 30)
	_sign("GATE 03 →", Vector3(5, 2.7, -23.8), 0, 36)

func _sign(text: String, pos: Vector3, yaw: float, font_size: int) -> void:
	var label := Label3D.new()
	label.text = text
	label.position = pos
	label.rotation_degrees.y = yaw
	label.font_size = font_size
	label.pixel_size = 0.012
	label.modulate = Color("d3ceb6")
	label.outline_size = 3
	add_child(label)

func _lamp(pos: Vector3, color: Color, energy: float, radius: float) -> void:
	var light := OmniLight3D.new()
	light.position = pos
	light.light_color = color
	light.light_energy = energy
	light.omni_range = radius
	add_child(light)
	var bulb := _box("灯具", Vector3(1.4, 0.08, 0.25), pos + Vector3.UP * 0.25, "paper", false)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 2
	bulb.get_child(0).material_override = mat

func _lighting() -> void:
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("171e23")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("9faeae")
	env.ambient_light_energy = 0.65
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = env
	add_child(world)
	for z in [-16, 0, 16]:
		for x in [-5, 6]:
			_lamp(Vector3(x, 7, z), Color("e9c98a"), 2.8, 16)
		# Cold roof lights cast actual geometry shadows down into the working aisle.
		var light := SpotLight3D.new()
		light.position = Vector3(-2, 9.6, z)
		light.rotation_degrees.x = -90
		light.spot_angle = 65
		light.spot_range = 25
		light.light_energy = 3.2
		light.light_color = Color("b9d4e4")
		light.shadow_enabled = true
		add_child(light)
		_box("天窗框", Vector3(7, 0.1, 3.5), Vector3(-2, 9.75, z), "steel", false)
		for x in [-4.6, -2.8, -1.0, 0.8]:
			var glass := _box("天窗玻璃", Vector3(1.65, 0.12, 3.2), Vector3(x, 9.65, z), "paper", false)
			var mat := StandardMaterial3D.new()
			mat.albedo_color = Color("a0b8c4")
			mat.emission_enabled = true
			mat.emission = Color("718c9d")
			glass.get_child(0).material_override = mat
	for z in [-16, -4, 17]:
		_lamp(Vector3(-20, 5.5, z), Color("a3c7cb"), 1.6, 10)
	for z in [-16, -8, 0]:
		_lamp(Vector3(19, 6.9, z), Color("d4d9b7"), 1.3, 7)

func _loot_box(pos: Vector3, title: String, item: String, material: String) -> void:
	var root := _box(title, Vector3(1.0, 0.6, 0.7), pos, material)
	_box("箱盖", Vector3(1.06, 0.1, 0.76), pos + Vector3.UP * 0.33, "steel")
	_box("锁扣", Vector3(0.13, 0.24, 0.05), pos + Vector3(0, 0.1, 0.38), "yellow", false)
	loot.append({"node": root, "position": pos, "title": title, "item": item, "taken": false})
