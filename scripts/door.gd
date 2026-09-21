extends Node3D

var title := "门"
var opened := false
var locked := false
var busy := false
var leaf: StaticBody3D

func _ready() -> void:
	leaf = StaticBody3D.new()
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(1.5, 2.45, 0.12)
	mesh.mesh = box
	mesh.position = Vector3(0.75, 1.225, 0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("526659")
	mat.roughness = 0.85
	mesh.material_override = mat
	leaf.add_child(mesh)
	var shape := CollisionShape3D.new()
	var collision := BoxShape3D.new()
	collision.size = box.size
	shape.shape = collision
	shape.position = mesh.position
	leaf.add_child(shape)
	add_child(leaf)

func target_position() -> Vector3:
	return to_global(Vector3(0.75, 1.1, 0))

func interact(has_key: bool) -> bool:
	if busy: return false
	if locked and not has_key: return false
	locked = false
	busy = true
	opened = not opened
	var tween := create_tween()
	tween.tween_property(leaf, "rotation:y", PI * 0.5 if opened else 0.0, 0.55)
	tween.finished.connect(func(): busy = false)
	return true
