extends Area3D

var owner_enemy: TrainingEnemy

func receive_bullet(base_damage: float, _hit_position: Vector3) -> void:
	if is_instance_valid(owner_enemy):
		owner_enemy.apply_damage(base_damage * float(get_meta("multiplier", 1.0)), str(get_meta("part", "躯干")))
