extends Node3D

var velocity := Vector3.ZERO
var shooter: CollisionObject3D
var damage := 48.0
var penetration := 28.0
var age := 0.0

func _physics_process(delta: float) -> void:
	age += delta
	if age > 2:
		queue_free()
		return
	var destination := global_position + velocity * delta
	var query := PhysicsRayQueryParameters3D.create(global_position, destination)
	query.collision_mask = 7
	if is_instance_valid(shooter): query.exclude = [shooter]
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit:
		if hit.collider.has_method("receive_bullet"):
			hit.collider.receive_bullet(damage, hit.position, penetration)
		if is_instance_valid(shooter) and shooter.has_method("_spawn_impact"): shooter._spawn_impact(hit.position, hit.normal)
		queue_free()
		return
	global_position = destination
	velocity.y -= 9.81 * delta
