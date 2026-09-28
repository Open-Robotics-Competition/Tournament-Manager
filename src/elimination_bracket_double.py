"""Double-elimination bracket topology (FRC/FTC-style 8-alliance format), with a
possible bracket-reset grand final counted as always played."""

try:
	from . import elimination_bracket_common as common
except ImportError:
	import elimination_bracket_common as common


def _raw_topology(size: int) -> list[tuple]:
	if size == 8:
		return [
			("M", ("seed", 1), ("seed", 8), "WB", 1),      # 0
			("M", ("seed", 4), ("seed", 5), "WB", 1),       # 1
			("M", ("seed", 2), ("seed", 7), "WB", 1),       # 2
			("M", ("seed", 3), ("seed", 6), "WB", 1),       # 3
			("M", ("loser", 0), ("loser", 1), "LB", 1),     # 4
			("M", ("loser", 2), ("loser", 3), "LB", 1),     # 5
			("M", ("winner", 0), ("winner", 1), "WB", 2),   # 6
			("M", ("winner", 2), ("winner", 3), "WB", 2),   # 7
			("M", ("winner", 4), ("loser", 7), "LB", 2),    # 8
			("M", ("winner", 5), ("loser", 6), "LB", 2),    # 9
			("M", ("winner", 8), ("winner", 9), "LB", 3),   # 10
			("M", ("winner", 6), ("winner", 7), "WB", 3),   # 11
			("M", ("winner", 10), ("loser", 11), "LB", 4),  # 12
			("F", ("winner", 11), ("winner", 12), "GF", 1),  # 13
			("F", ("winner", 11), ("winner", 12), "GF", 2),  # 14 (reset, same participants)
		]
	if size == 4:
		return [
			("M", ("seed", 1), ("seed", 4), "WB", 1),      # 0
			("M", ("seed", 2), ("seed", 3), "WB", 1),      # 1
			("M", ("loser", 0), ("loser", 1), "LB", 1),    # 2
			("M", ("winner", 0), ("winner", 1), "WB", 2),  # 3
			("M", ("winner", 2), ("loser", 3), "LB", 2),   # 4
			("F", ("winner", 3), ("winner", 4), "GF", 1),  # 5
			("F", ("winner", 3), ("winner", 4), "GF", 2),  # 6 (reset)
		]
	return [
		("M", ("seed", 1), ("seed", 2), "WB", 1),  # 0
		("F", ("winner", 0), ("loser", 0), "GF", 1),  # 1
		("F", ("winner", 0), ("loser", 0), "GF", 2),  # 2 (reset)
	]


def build_topology(alliance_count: int) -> list[dict]:
	size = common.bracket_size_for(alliance_count)
	topology = []
	counters = {"M": 0, "F": 0}
	for match_type, red, blue, group, round_number in _raw_topology(size):
		counters[match_type] += 1
		topology.append({
			"match_type": match_type, "match_number": counters[match_type],
			"red": red, "blue": blue, "group": group, "round": round_number,
		})
	return topology


def match_count(alliance_lookup: dict) -> int:
	return common.match_count(build_topology(len(alliance_lookup)), alliance_lookup)


def generate_bracket(state: dict) -> None:
	state["bracket_type"] = "double"
	state["bracket"] = []
	common.refresh_bracket(state, build_topology)
