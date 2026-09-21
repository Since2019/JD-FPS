class_name RaidVitals
extends RefCounted

const MAX_HP := {"head": 35.0, "thorax": 85.0, "stomach": 70.0, "left_arm": 60.0, "right_arm": 60.0, "left_leg": 65.0, "right_leg": 65.0}
const NAMES := {"head": "头部", "thorax": "胸部", "stomach": "腹部", "left_arm": "左臂", "right_arm": "右臂", "left_leg": "左腿", "right_leg": "右腿"}
var hp: Dictionary = MAX_HP.duplicate()
var wounds: Dictionary = {}
var armor := 50.0
var dead := false

func total() -> float:
	var result := 0.0
	for value in hp.values(): result += value
	return result

func leg_injured() -> bool:
	return hp.left_leg < 20 or hp.right_leg < 20

func arm_injured() -> bool:
	return hp.left_arm < 20 or hp.right_arm < 20

func hit(damage: float, part := "thorax", penetration := 28.0) -> float:
	if dead: return 0.0
	if not hp.has(part): part = "thorax"
	var dealt := damage
	if part in ["thorax", "stomach"] and armor > 0:
		var protection := clampf((40.0 - penetration) / 40.0, 0.0, 0.85) * (armor / 50.0)
		dealt *= 1.0 - protection
		armor = maxf(0, armor - damage * 0.24)
	var overflow := maxf(0, dealt - float(hp[part]))
	hp[part] = maxf(0, hp[part] - dealt)
	if part not in ["head", "thorax"] and overflow > 0:
		var eligible: Array[String] = []
		for key: String in hp:
			if key != part and hp[key] > 0: eligible.append(key)
		for key in eligible: hp[key] = maxf(0, hp[key] - overflow / eligible.size())
	if dealt > 25 and part not in ["head", "thorax"]: wounds[part] = true
	dead = hp.head <= 0 or hp.thorax <= 0
	return dealt

func tick(delta: float) -> void:
	if wounds.is_empty() or dead: return
	for key in hp:
		if hp[key] > 0: hp[key] = maxf(0, hp[key] - 0.09 * wounds.size() * delta)
	dead = hp.head <= 0 or hp.thorax <= 0

func heal() -> void:
	# Field treatment stops bleeding; destroyed limbs need surgery, not a medkit.
	wounds.clear()
	var worst := ""
	var fraction := 1.0
	for key: String in hp:
		if hp[key] > 0 and hp[key] / MAX_HP[key] < fraction:
			worst = key
			fraction = hp[key] / MAX_HP[key]
	if worst != "": hp[worst] = minf(MAX_HP[worst], hp[worst] + 60)

func description() -> String:
	var lines: Array[String] = []
	for key in hp:
		lines.append("%s  %d / %d%s" % [NAMES[key], hp[key], MAX_HP[key], "  失血" if wounds.has(key) else ("  损毁" if hp[key] == 0 else "")])
	return "\n".join(lines)
