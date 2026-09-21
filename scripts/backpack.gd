class_name RaidBackpack
extends RefCounted

const WIDTH := 6
const HEIGHT := 5
const ITEMS := {
	"医疗包": [2, 1, 0.6], "绷带": [1, 1, 0.1], "饮用水": [1, 2, 0.7],
	"机械零件": [2, 2, 1.8], "电钻": [2, 2, 2.5], "情报文件": [2, 1, 0.2],
	"工厂紧急出口钥匙": [1, 1, 0.1], "步枪弹药": [1, 1, 0.6],
	"战术背心": [3, 3, 6.0], "步枪": [4, 2, 3.5], "弹匣": [1, 2, 0.4]
}
var entries: Array[Dictionary] = []
var next_id := 1

func fits(x: int, y: int, w: int, h: int, ignore_id := -1) -> bool:
	if x < 0 or y < 0 or x + w > WIDTH or y + h > HEIGHT: return false
	for entry in entries:
		if entry.id == ignore_id: continue
		if Rect2i(x, y, w, h).intersects(Rect2i(entry.x, entry.y, entry.w, entry.h)): return false
	return true

func add(item: String, rounds := -1) -> bool:
	var spec: Array = ITEMS.get(item, [1, 1, 0.5])
	for y in HEIGHT:
		for x in WIDTH:
			if fits(x, y, spec[0], spec[1]):
				entries.append({"id": next_id, "name": item, "x": x, "y": y, "w": spec[0], "h": spec[1], "weight": spec[2], "rounds": rounds})
				next_id += 1
				return true
	return false

func has(item: String) -> bool:
	for entry in entries:
		if entry.name == item: return true
	return false

func find_item(item: String) -> int:
	for entry in entries:
		if entry.name == item: return entry.id
	return -1

func remove(id: int) -> Dictionary:
	for i in entries.size():
		if entries[i].id == id: return entries.pop_at(i)
	return {}

func rotate_item(id: int) -> bool:
	for entry in entries:
		if entry.id == id and fits(entry.x, entry.y, entry.h, entry.w, id):
			var old: int = entry.w
			entry.w = entry.h
			entry.h = old
			return true
	return false

func weight() -> float:
	var result := 0.0
	for entry in entries: result += entry.weight
	return result

func names() -> Array[String]:
	var result: Array[String] = []
	for entry in entries: result.append(entry.name)
	return result
