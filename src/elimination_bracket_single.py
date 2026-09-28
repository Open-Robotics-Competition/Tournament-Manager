"""Single-elimination bracket topology: rounds QF/SF/F, with a best-of-3 final (F1/F2/F3)."""

try:
	from . import elimination_bracket_common as common
except ImportError:
	import elimination_bracket_common as common

# Round-1 seed pairings by bracket size (standard tournament seeding).
_SEED_PAIRS = {
	2: [(1, 2)],
	4: [(1, 4), (2, 3)],
	8: [(1, 8), (4, 5), (2, 7), (3, 6)],
}


def build_topology(alliance_count: int) -> list[dict]:
	size = common.bracket_size_for(alliance_count)
	topology = []

	if size == 8:
		for index, (a, b) in enumerate(_SEED_PAIRS[8]):
			topology.append({
				"match_type": "QF", "match_number": index + 1,
				"red": ("seed", a), "blue": ("seed", b), "group": "MAIN", "round": 1,
			})
		topology.append({
			"match_type": "SF", "match_number": 1, "red": ("winner", 0), "blue": ("winner", 1),
			"group": "MAIN", "round": 2,
		})
		topology.append({
			"match_type": "SF", "match_number": 2, "red": ("winner", 2), "blue": ("winner", 3),
			"group": "MAIN", "round": 2,
		})
		final_red, final_blue, final_round = ("winner", 4), ("winner", 5), 3
	elif size == 4:
		for index, (a, b) in enumerate(_SEED_PAIRS[4]):
			topology.append({
				"match_type": "SF", "match_number": index + 1,
				"red": ("seed", a), "blue": ("seed", b), "group": "MAIN", "round": 1,
			})
		final_red, final_blue, final_round = ("winner", 0), ("winner", 1), 2
	else:
		final_red, final_blue, final_round = ("seed", 1), ("seed", 2), 1

	for game in range(1, 4):
		topology.append({
			"match_type": "F", "match_number": game, "red": final_red, "blue": final_blue,
			"group": "MAIN", "round": final_round,
		})

	return topology


def match_count(alliance_lookup: dict) -> int:
	return common.match_count(build_topology(len(alliance_lookup)), alliance_lookup)


def generate_bracket(state: dict) -> None:
	state["bracket_type"] = "single"
	state["bracket"] = []
	common.refresh_bracket(state, build_topology)
