"""Shared engine + UI for the elimination bracket, used by both single and double elimination."""

import csv
from pathlib import Path

import pyglet
from pyglet import gl

try:
	from .Match import Match
	from . import tournament_setup
except ImportError:
	from Match import Match
	import tournament_setup

WHITE = (255, 255, 255)
PANEL = (38, 43, 50)
ROW_A = (45, 51, 59)
ROW_B = (35, 40, 47)
ROW_RED_WIN = (92, 35, 35)
ROW_BLUE_WIN = (30, 40, 90)
ROW_TIE = (70, 70, 76)
BUTTON = (65, 93, 120)
BUTTON_DISABLED = (55, 58, 62)
GOLD = (255, 204, 0)
BRACKET_FILENAME = "bracket.txt"
FIELD_WIDTH = 1920
FIELD_HEIGHT = 1080
CONNECTOR_LINE_WIDTH = 5
MIN_BOX_WIDTH_FRACTION = 0.075  # box width floor for match boxes, which only show short labels
BRACKET_AREA_FRACTION = 0.74  # matches/brackets are confined to this much of the width; the rest is the alliance table
FINAL_STACK_GAP_FRACTION = 0.02  # vertical gap between stacked finals-series boxes (F1/F2/F3, GF1/GF2)


def get_alliance_lookup(state: dict) -> dict[int, tuple[int, int]]:
	"""Seed (1-based, matching alliance slot order) -> (team_1, team_2) for filled alliances."""
	lookup = {}
	for index, alliance in enumerate(state["alliance_state"]["alliances"]):
		if alliance[0] is not None:
			lookup[index + 1] = (alliance[0], alliance[1] if alliance[1] is not None else alliance[0])
	return lookup


def bracket_size_for(count: int) -> int:
	for size in (2, 4, 8):
		if count <= size:
			return size
	return 8


def _resolve_side(ref, alliance_lookup, resolved):
	kind, value = ref
	if kind == "seed":
		pair = alliance_lookup.get(value)
		return "BYE" if pair is None else pair
	info = resolved.get(value)
	if info is None:
		return None
	if info["bye"] and kind == "loser":
		return "BYE"
	return info[kind]


def resolve_bracket(topology: list[dict], alliance_lookup: dict, previous_by_batch: dict) -> list[Match]:
	resolved = {}
	matches = []
	for index, entry in enumerate(topology):
		red = _resolve_side(entry["red"], alliance_lookup, resolved)
		blue = _resolve_side(entry["blue"], alliance_lookup, resolved)

		if red == "BYE" and blue == "BYE":
			resolved[index] = {"winner": None, "loser": None, "bye": True}
			continue
		if red == "BYE" or blue == "BYE":
			concrete = blue if red == "BYE" else red
			resolved[index] = {"winner": concrete, "loser": None, "bye": True}
			continue

		previous = previous_by_batch.get(index)
		match = Match()
		match.batch = index
		match.match_type = entry["match_type"]
		match.match_number = entry["match_number"]
		match.red_team_1, match.red_team_2 = red if red is not None else (-1, -1)
		match.blue_team_1, match.blue_team_2 = blue if blue is not None else (-1, -1)
		if previous is not None:
			match.red_score = previous.red_score
			match.blue_score = previous.blue_score
			match.red_rp = previous.red_rp
			match.blue_rp = previous.blue_rp
			match.played = previous.played
			match.red_breakdown = previous.red_breakdown
			match.blue_breakdown = previous.blue_breakdown
		matches.append(match)

		if previous is not None and previous.played and red is not None and blue is not None:
			if previous.red_score >= previous.blue_score:
				resolved[index] = {"winner": red, "loser": blue, "bye": False}
			else:
				resolved[index] = {"winner": blue, "loser": red, "bye": False}
		else:
			resolved[index] = {"winner": None, "loser": None, "bye": False}

	# Byes remove whichever seed pairing lacks an opponent, which can leave gaps in the
	# numbering (e.g. QF1 skipped, QF2-4 remain). Renumber within each match_type so the
	# surviving matches are always 1..N and it's effectively the highest numbers that vanish.
	type_counters: dict[str, int] = {}
	for match in matches:
		type_counters[match.match_type] = type_counters.get(match.match_type, 0) + 1
		match.match_number = type_counters[match.match_type]
	return matches


def match_count(topology: list[dict], alliance_lookup: dict) -> int:
	return len(resolve_bracket(topology, alliance_lookup, {}))


def refresh_bracket(state: dict, build_topology) -> None:
	"""Recompute state["bracket"] from scratch, preserving previously played results."""
	alliance_lookup = get_alliance_lookup(state)
	topology = build_topology(len(alliance_lookup))
	previous_by_batch = {match.batch: match for match in state["bracket"]}
	state["bracket"] = resolve_bracket(topology, alliance_lookup, previous_by_batch)


def write_bracket(state: dict) -> Path:
	output_path = Path(tournament_setup.tournament_data_path) / BRACKET_FILENAME
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8") as bracket_file:
		bracket_file.write(f"{state['bracket_type']}\n")
		writer = csv.writer(bracket_file)
		writer.writerow((
			"batch", "match_type", "match_number",
			"red_team_1", "red_team_2", "blue_team_1", "blue_team_2",
			"red_score", "blue_score", "red_rp", "blue_rp", "played",
			"red_breakdown", "blue_breakdown",
		))
		for match in state["bracket"]:
			writer.writerow((
				match.batch, match.match_type, match.match_number,
				match.red_team_1, match.red_team_2, match.blue_team_1, match.blue_team_2,
				match.red_score, match.blue_score, match.red_rp, match.blue_rp, match.played,
				_serialize_breakdown(match.red_breakdown), _serialize_breakdown(match.blue_breakdown),
			))
	return output_path


def _serialize_breakdown(breakdown):
	if not breakdown:
		return ""
	keys = ("goal", "exc", "p1", "p2", "major_foul", "minor_foul")
	return ";".join(f"{key}:{breakdown.get(key, 0)}" for key in keys)


def _deserialize_breakdown(text):
	if not text:
		return None
	breakdown = {}
	for part in text.split(";"):
		key, _, value = part.partition(":")
		if key:
			breakdown[key] = int(value) if value else 0
	return breakdown


def read_bracket(tournament_data_path: str):
	"""Returns (bracket_type, matches) parsed from bracket.txt, or None if unreadable."""
	input_path = Path(tournament_data_path) / BRACKET_FILENAME
	if not input_path.exists():
		return None
	try:
		with input_path.open("r", newline="", encoding="utf-8") as bracket_file:
			bracket_type = bracket_file.readline().strip()
			if bracket_type not in ("single", "double"):
				return None
			reader = csv.DictReader(bracket_file)
			matches = []
			for row in reader:
				match = Match()
				match.batch = int(row["batch"])
				match.match_type = row["match_type"]
				match.match_number = int(row["match_number"])
				match.red_team_1 = int(row["red_team_1"])
				match.red_team_2 = int(row["red_team_2"])
				match.blue_team_1 = int(row["blue_team_1"])
				match.blue_team_2 = int(row["blue_team_2"])
				match.red_score = int(row["red_score"])
				match.blue_score = int(row["blue_score"])
				match.red_rp = int(row["red_rp"])
				match.blue_rp = int(row["blue_rp"])
				match.played = row["played"] in ("True", "true", "1")
				match.red_breakdown = _deserialize_breakdown(row.get("red_breakdown", ""))
				match.blue_breakdown = _deserialize_breakdown(row.get("blue_breakdown", ""))
				matches.append(match)
	except (OSError, ValueError, KeyError):
		return None
	return bracket_type, matches


def bracket_file_available() -> bool:
	return (Path(tournament_setup.tournament_data_path) / BRACKET_FILENAME).exists()


def row_color(match: Match) -> tuple:
	if not match.played:
		return None
	if match.red_score > match.blue_score:
		return ROW_RED_WIN
	if match.blue_score > match.red_score:
		return ROW_BLUE_WIN
	return ROW_TIE


def _team_name(team_id, teams):
	if team_id is None or team_id < 0:
		return "TBD"
	for team in teams:
		if team.eventID == team_id:
			return team.name
	return f"Unknown team {team_id}"


def is_most_recent_played(state: dict, match: Match) -> bool:
	"""A played match can only be edited if no later-played match exists (by batch order)."""
	if not match.played:
		return True
	later_played = [m for m in state["bracket"] if m.batch > match.batch and m.played]
	return not later_played


def get_placements(state: dict):
	"""Returns {"first":(t1,t2), "second":(t1,t2), "third":[(t1,t2), ...]} once decided, else None."""
	bracket = state["bracket"]
	if not bracket or state["bracket_type"] is None:
		return None

	if state["bracket_type"] == "single":
		finals = sorted((m for m in bracket if m.match_type == "F"), key=lambda m: m.match_number)
		played_finals = [m for m in finals if m.played]
		if not played_finals:
			return None
		red_wins = sum(1 for m in played_finals if m.red_score > m.blue_score)
		blue_wins = sum(1 for m in played_finals if m.blue_score > m.red_score)
		if red_wins < 2 and blue_wins < 2:
			return None
		last = played_finals[0]
		champion_is_red = red_wins >= 2
		first_place = (last.red_team_1, last.red_team_2) if champion_is_red else (last.blue_team_1, last.blue_team_2)
		second_place = (last.blue_team_1, last.blue_team_2) if champion_is_red else (last.red_team_1, last.red_team_2)
		third_place = []
		for match in bracket:
			if match.match_type != "SF":
				continue
			if not match.played:
				return None
			loser = (
				(match.blue_team_1, match.blue_team_2) if match.red_score > match.blue_score
				else (match.red_team_1, match.red_team_2)
			)
			third_place.append(loser)
		return {"first": first_place, "second": second_place, "third": third_place}

	finals = sorted((m for m in bracket if m.match_type == "F"), key=lambda m: m.match_number)
	if not finals or not finals[0].played:
		return None
	decisive = finals[1] if len(finals) > 1 and finals[1].played else finals[0]
	champion_is_red = decisive.red_score > decisive.blue_score
	first_place = (decisive.red_team_1, decisive.red_team_2) if champion_is_red else (decisive.blue_team_1, decisive.blue_team_2)
	second_place = (decisive.blue_team_1, decisive.blue_team_2) if champion_is_red else (decisive.red_team_1, decisive.red_team_2)
	m_matches = [m for m in bracket if m.match_type == "M"]
	third_place = []
	if len(m_matches) > 1:
		lb_final = max(m_matches, key=lambda m: m.match_number)
		if lb_final.played:
			loser = (
				(lb_final.blue_team_1, lb_final.blue_team_2) if lb_final.red_score > lb_final.blue_score
				else (lb_final.red_team_1, lb_final.red_team_2)
			)
			third_place = [loser]
	return {"first": first_place, "second": second_place, "third": third_place}


def create_controls(state: dict, font_name: str, window, build_topology, on_run=None, on_edit=None):
	scale_x = window.width / 900
	panel = pyglet.shapes.RoundedRectangle(
		40 * scale_x, 95, 820 * scale_x, 555, radius=10 * scale_x, color=PANEL
	)
	heading = pyglet.text.Label(
		"ELIMINATION BRACKET", font_name=font_name, font_size=30, weight="bold",
		x=450 * scale_x, y=620, anchor_x="center", anchor_y="center", color=WHITE,
	)
	load_button = pyglet.shapes.RoundedRectangle(
		640 * scale_x, 595, 190 * scale_x, 40, radius=6 * scale_x, color=(54, 104, 151),
	)
	load_label = pyglet.text.Label(
		"LOAD BRACKET", font_name=font_name, font_size=14, weight="bold",
		x=735 * scale_x, y=615, anchor_x="center", anchor_y="center", color=WHITE,
	)

	viewport_bottom = 145
	viewport_top = 580
	row_height = 76
	visible_rows = 5
	scroll_offset = 0
	rows = []
	last_signature = None

	def load_bracket():
		if state["bracket_type"] is None:
			return
		result = read_bracket(tournament_setup.tournament_data_path)
		if result is None:
			return
		bracket_type, matches = result
		if bracket_type != state["bracket_type"]:
			return
		alliance_lookup = get_alliance_lookup(state)
		expected_count = match_count(build_topology(len(alliance_lookup)), alliance_lookup)
		if len(matches) != expected_count:
			return
		state["bracket"] = matches

	def refresh_rows():
		nonlocal rows, last_signature
		bracket = state["bracket"]
		signature = tuple(
			(m.batch, m.red_team_1, m.red_team_2, m.blue_team_1, m.blue_team_2,
			 m.red_score, m.blue_score, m.played)
			for m in bracket
		)
		if signature == last_signature:
			return
		last_signature = signature
		rows = []
		for index, match in enumerate(bracket):
			y = viewport_top - index * row_height - row_height
			background = pyglet.shapes.Rectangle(
				50 * scale_x, y, 800 * scale_x, row_height - 5,
				color=ROW_A if index % 2 == 0 else ROW_B,
			)
			label = pyglet.text.Label(
				f"{match.match_type}{match.match_number}", font_name=font_name, font_size=17,
				weight="bold", x=65 * scale_x, y=y + 35, anchor_x="left", anchor_y="center", color=WHITE,
			)
			names = pyglet.text.Label(
				f"{_team_name(match.red_team_1, state['teams'])} / {_team_name(match.red_team_2, state['teams'])}"
				f"\nvs {_team_name(match.blue_team_1, state['teams'])} / {_team_name(match.blue_team_2, state['teams'])}",
				font_name=font_name, font_size=14, x=170 * scale_x, y=y + 36,
				width=390 * scale_x, multiline=True, align="left",
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			score = pyglet.text.Label(
				f"{max(0, match.red_score)}-{max(0, match.blue_score)}" if match.played else "-",
				font_name=font_name, font_size=18, weight="bold", x=595 * scale_x, y=y + 35,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			run_button = pyglet.shapes.RoundedRectangle(
				650 * scale_x, y + 13, 90 * scale_x, 44, radius=5, color=BUTTON,
			)
			run_label = pyglet.text.Label(
				"RUN", font_name=font_name, font_size=14, weight="bold",
				x=695 * scale_x, y=y + 35, anchor_x="center", anchor_y="center", color=WHITE,
			)
			edit_button = pyglet.shapes.RoundedRectangle(
				755 * scale_x, y + 13, 90 * scale_x, 44, radius=5, color=BUTTON,
			)
			edit_label = pyglet.text.Label(
				"EDIT", font_name=font_name, font_size=14, weight="bold",
				x=800 * scale_x, y=y + 35, anchor_x="center", anchor_y="center", color=WHITE,
			)
			rows.append((
				match, background, label, names, score,
				run_button, run_label, edit_button, edit_label,
			))

	def draw():
		window.switch_to()
		window.clear()
		panel.draw()
		heading.draw()
		load_button.color = (54, 104, 151) if bracket_file_available() else BUTTON_DISABLED
		load_button.draw()
		load_label.draw()
		refresh_rows()
		max_offset = max(0, len(rows) - visible_rows)
		first_row = min(scroll_offset, max_offset)
		vertical_shift = first_row * row_height
		# Recompute gating/colors for every row so state stays correct even while scrolled away.
		for index, row in enumerate(rows):
			match, background, label, names, score, run_button, run_label, edit_button, edit_label = row
			ready = match.red_team_1 >= 0 and match.blue_team_1 >= 0
			locked = match.played and not is_most_recent_played(state, match)
			color = row_color(match)
			background.color = color if color is not None else (ROW_A if index % 2 == 0 else ROW_B)
			run_button.color = BUTTON if (ready and not locked) else BUTTON_DISABLED
			edit_button.color = BUTTON if (match.played and not locked) else BUTTON_DISABLED
		for row in rows[first_row:first_row + visible_rows]:
			_match, background, label, names, score, run_button, run_label, edit_button, edit_label = row
			for element in (background, label, names, score, run_button, run_label, edit_button, edit_label):
				element.y += vertical_shift
				element.draw()
				element.y -= vertical_shift

	def handle_click(x, y, button, modifiers):
		if (
			load_button.x <= x <= load_button.x + load_button.width
			and load_button.y <= y <= load_button.y + load_button.height
			and bracket_file_available()
		):
			load_bracket()
			return True
		max_offset = max(0, len(rows) - visible_rows)
		first_row = min(scroll_offset, max_offset)
		vertical_shift = first_row * row_height
		for row in rows[first_row:first_row + visible_rows]:
			match, _background, _label, _names, _score, run_button, _run_label, edit_button, _edit_label = row
			ready = match.red_team_1 >= 0 and match.blue_team_1 >= 0
			locked = match.played and not is_most_recent_played(state, match)
			if (
				ready and not locked
				and run_button.x <= x <= run_button.x + run_button.width
				and run_button.y + vertical_shift <= y <= run_button.y + vertical_shift + run_button.height
			):
				if on_run is not None:
					on_run(match)
				return True
			if (
				match.played and not locked
				and edit_button.x <= x <= edit_button.x + edit_button.width
				and edit_button.y + vertical_shift <= y <= edit_button.y + vertical_shift + edit_button.height
			):
				if on_edit is not None:
					on_edit(match)
				return True
		return False

	def handle_scroll(x, y, scroll_x, scroll_y):
		nonlocal scroll_offset
		max_offset = max(0, len(rows) - visible_rows)
		scroll_offset = min(max(0, scroll_offset - int(scroll_y)), max_offset)
		return True

	return draw, handle_click, handle_scroll


BOX_GREY = (70, 74, 80)


def box_color(match: Match) -> tuple:
	color = row_color(match)
	if color is None or color == ROW_TIE:
		return BOX_GREY
	return color


def _slot_text(ref, team_1, team_2, matches_by_batch, alliance_by_pair):
	if team_1 is not None and team_1 >= 0:
		seed = alliance_by_pair.get(frozenset((team_1, team_2)))
		return f"ALLIANCE {seed}" if seed is not None else "ALLIANCE"
	kind, value = ref
	source = matches_by_batch.get(value)
	if source is not None:
		verb = "Winner" if kind == "winner" else "Loser"
		return f"{verb} of {source.match_type}{source.match_number}"
	return "TBD"


def _build_edges(topology):
	"""One incoming edge per feed, except repeated-participant series (best-of-3 finals,
	grand-final reset) which only connect into the first game, then chain game-to-game."""
	edges = []
	previous_index_by_key = {}
	for index, entry in enumerate(topology):
		key = (entry["match_type"], entry["red"], entry["blue"])
		if key in previous_index_by_key:
			edges.append((previous_index_by_key[key], index))
		else:
			for ref in (entry["red"], entry["blue"]):
				kind, value = ref
				if kind == "winner":
					edges.append((value, index))
		previous_index_by_key[key] = index
	return edges


def create_field_renderer(window, state: dict, font_name: str, build_topology):
	width = window.width
	height = window.height
	bracket_width = width * BRACKET_AREA_FRACTION
	background = pyglet.shapes.Rectangle(0, 0, width, height, color=(18, 20, 25))
	heading = pyglet.text.Label(
		"ELIMINATION BRACKET", font_name=font_name, font_size=int(40 * height / 1080), weight="bold",
		x=width * 0.015, y=height * 0.97, anchor_x="left", anchor_y="center", color=WHITE,
	)
	logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	logo = pyglet.sprite.Sprite(logo_image)

	def _column_centers(num_columns, box_w):
		"""Evenly spreads num_columns box-centers across the bracket area, edge-to-edge with margin."""
		margin = bracket_width * 0.02
		if num_columns <= 1:
			return [bracket_width / 2]
		pitch = (bracket_width - 2 * margin - box_w) / (num_columns - 1)
		return [margin + box_w / 2 + column * pitch for column in range(num_columns)]

	def _grown_box_width(num_columns, base_box_w, gap_scale):
		"""Box width that fills the same total span as base_box_w but with gap_scale x the gap."""
		margin = bracket_width * 0.02
		gap_count = num_columns - 1
		if gap_count <= 0:
			return base_box_w
		base_gap = (bracket_width - 2 * margin - base_box_w) / gap_count - base_box_w
		new_gap = base_gap * gap_scale
		return (bracket_width - 2 * margin - gap_count * new_gap) / (1 + gap_count)

	def _layout_group(indices_by_round, center_x_by_round, box_w, y_top, y_bottom):
		"""Places each round's matches in its aligned column, evenly stacked within [y_bottom, y_top]."""
		positions = {}
		for round_number, indices in indices_by_round.items():
			center_x = center_x_by_round[round_number]
			slot_height = (y_top - y_bottom) / len(indices)
			for row, batch_index in enumerate(indices):
				center_y = y_top - (row + 0.5) * slot_height
				box_h = min(slot_height * 0.72, height * 0.12)
				positions[batch_index] = (center_x, center_y, box_w, box_h)
		return positions

	def _compute_layout(topology):
		base_box_w = width * MIN_BOX_WIDTH_FRACTION
		if state["bracket_type"] == "double":
			wb_rounds: dict[int, list[int]] = {}
			lb_rounds: dict[int, list[int]] = {}
			gf_indices = []
			for index, entry in enumerate(topology):
				group = entry.get("group")
				if group == "WB":
					wb_rounds.setdefault(entry["round"], []).append(index)
				elif group == "LB":
					lb_rounds.setdefault(entry["round"], []).append(index)
				elif group == "GF":
					gf_indices.append((entry["round"], index))

			# Winner- and loser-bracket rounds share the same columns so round 1/2/3 of each
			# align vertically. The loser-bracket final has no matching WB round; rather than
			# reserving it a whole column, it shares the last aligned column (the round before
			# it, right underneath) and sits vertically in line with F2.
			aligned_rounds = sorted(wb_rounds) or sorted(lb_rounds)
			num_columns = max(1, len(aligned_rounds))
			total_columns = num_columns + 1  # winner/loser-bracket columns plus the finals column
			box_w = _grown_box_width(total_columns, base_box_w, 0.5)
			centers = _column_centers(total_columns, box_w)

			column_of_round = dict(zip(aligned_rounds, centers[:num_columns]))
			positions = {}
			positions.update(_layout_group(wb_rounds, column_of_round, box_w, height * 0.93, height * 0.56))
			aligned_lb_rounds = {r: v for r, v in lb_rounds.items() if r in column_of_round}
			positions.update(_layout_group(aligned_lb_rounds, column_of_round, box_w, height * 0.44, height * 0.07))

			gf_indices.sort()
			gf_center_x = centers[-1]
			gf_box_h = box_w * 0.4
			gf_center_ys = []
			for order, (_round_number, index) in enumerate(gf_indices):
				center_y = height * 0.53 - order * (gf_box_h + height * FINAL_STACK_GAP_FRACTION)
				positions[index] = (gf_center_x, center_y, box_w, gf_box_h)
				gf_center_ys.append(center_y)

			last_round = max(aligned_rounds, default=0)
			final_center_x = column_of_round.get(last_round, gf_center_x)
			extra_lb_rounds = sorted(r for r in lb_rounds if r not in column_of_round)
			for offset, round_number in enumerate(extra_lb_rounds):
				f2_index = min(offset + 1, len(gf_center_ys) - 1) if gf_center_ys else 0
				center_y = gf_center_ys[f2_index] if gf_center_ys else height * 0.48
				for batch_index in lb_rounds[round_number]:
					positions[batch_index] = (final_center_x, center_y, box_w, gf_box_h)
			return positions

		# Single elimination: normal rounds get even columns, with half the current gap
		# between them (freeing width spent on larger boxes); the finals series (F1/F2/F3)
		# stacks vertically with F1 at screen-center instead of spreading across full height.
		rounds: dict[int, list[int]] = {}
		for index, entry in enumerate(topology):
			rounds.setdefault(entry["round"], []).append(index)
		if not rounds:
			return {}
		final_indices = rounds.pop(max(rounds), [])
		num_columns = len(rounds) + 1
		box_w = _grown_box_width(num_columns, base_box_w, 0.5)
		centers = _column_centers(num_columns, box_w)
		column_of_round = dict(zip(sorted(rounds), centers[:-1]))
		positions = _layout_group(rounds, column_of_round, box_w, height * 0.90, height * 0.06)

		final_center_x = centers[-1]
		final_box_h = box_w * 0.4
		for order, batch_index in enumerate(final_indices):
			center_y = height * 0.5 - order * (final_box_h + height * FINAL_STACK_GAP_FRACTION)
			positions[batch_index] = (final_center_x, center_y, box_w, final_box_h)
		return positions

	def _draw_alliance_table(alliance_lookup, teams):
		"""Alliance number + team name reference table, confined to the top-right corner."""
		table_left = bracket_width + width * 0.015
		table_right = width * 0.99
		table_width = table_right - table_left
		seeds = sorted(alliance_lookup)
		if not seeds:
			return
		header = pyglet.text.Label(
			"ALLIANCES", font_name=font_name, font_size=int(26 * height / 1080), weight="bold",
			x=table_left + table_width / 2, y=height * 0.97, anchor_x="center", anchor_y="center", color=GOLD,
		)
		header.draw()
		row_height = min(height * 0.11, (height * 0.90) / len(seeds))
		title_w = table_width * 0.22
		teams_w = table_width - title_w
		font_size = max(8, min(int(row_height * 0.24), int(teams_w * 0.033)))
		for row, seed in enumerate(seeds):
			team_1, team_2 = alliance_lookup[seed]
			center_y = height * 0.91 - row * row_height
			title_label = pyglet.text.Label(
				f"A{seed}", font_name=font_name, font_size=font_size, weight="bold",
				x=table_left + title_w / 2, y=center_y, anchor_x="center", anchor_y="center", color=GOLD,
			)
			teams_label = pyglet.text.Label(
				f"{_team_name(team_1, teams)}\n{_team_name(team_2, teams)}",
				font_name=font_name, font_size=font_size, weight="bold",
				x=table_left + title_w + teams_w / 2, y=center_y, width=teams_w * 0.96,
				multiline=True, align="left", anchor_x="center", anchor_y="center", color=WHITE,
			)
			title_label.draw()
			teams_label.draw()

	def draw():
		window.switch_to()
		window.clear()
		background.draw()
		heading.draw()
		bracket = state["bracket"]
		if not bracket:
			return
		alliance_lookup = get_alliance_lookup(state)
		topology = build_topology(len(alliance_lookup))
		positions = _compute_layout(topology)
		matches_by_batch = {match.batch: match for match in bracket}
		teams = state["teams"]
		alliance_by_pair = {frozenset(pair): seed for seed, pair in alliance_lookup.items()}
		_draw_alliance_table(alliance_lookup, teams)

		# All boxes render at the same size: the tightest slot in the layout.
		box_w = min(entry[2] for entry in positions.values())
		box_h = min(entry[3] for entry in positions.values())
		radius = min(box_w, box_h) * 0.16

		# Logo sits above the finals column, sized to fill the gap without touching anything else.
		finals_indices = (
			[i for i, e in enumerate(topology) if e.get("group") == "GF"] if state["bracket_type"] == "double"
			else [i for i, e in enumerate(topology) if e["match_type"] == "F"]
		)
		finals_positions = [positions[i] for i in finals_indices if i in positions]
		if finals_positions:
			finals_center_x = finals_positions[0][0]
			finals_top_y = max(entry_y + entry_h / 2 for _x, entry_y, _w, entry_h in finals_positions)
			logo_bottom = finals_top_y + height * 0.015
			logo_top = height * 0.965
			logo_size = max(0.0, min(logo_top - logo_bottom, box_w * 1.3))
			if logo_size > 0:
				logo.scale_x = logo_size / logo_image.width
				logo.scale_y = logo_size / logo_image.height
				logo.x = finals_center_x - logo_size / 2
				logo.y = logo_bottom
				logo.draw()

		# Connector lines first so boxes render on top of them; skip winner-to-loser-bracket
		# feeds, and skip any edge touching a bye-skipped (never-created) match.
		for src_index, dst_index in _build_edges(topology):
			if src_index not in matches_by_batch or dst_index not in matches_by_batch:
				continue
			src_x, src_y, _w, _h = positions[src_index]
			dst_x, dst_y, _w, _h = positions[dst_index]
			start_x = src_x + (box_w / 2 if dst_x >= src_x else -box_w / 2)
			end_x = dst_x - (box_w / 2 if dst_x >= src_x else -box_w / 2)
			line = pyglet.shapes.Line(
				start_x, src_y, end_x, dst_y, thickness=CONNECTOR_LINE_WIDTH, color=(110, 114, 120)
			)
			line.draw()

		for index, (center_x, center_y, _slot_w, _slot_h) in positions.items():
			match = matches_by_batch.get(index)
			if match is None:
				continue
			box_left = center_x - box_w / 2
			box_bottom = center_y - box_h / 2
			box = pyglet.shapes.RoundedRectangle(
				box_left, box_bottom, box_w, box_h, radius=radius, color=box_color(match)
			)
			box.draw()

			title_w = box_w * 0.22
			score_w = box_w * 0.20
			teams_w = box_w - title_w - score_w
			font_size = max(8, min(int(box_h * 0.20), int(box_w * 0.09)))
			teams_font_size = max(7, int(font_size * 0.75))
			entry = topology[index]

			title_label = pyglet.text.Label(
				f"{match.match_type}{match.match_number}", font_name=font_name, font_size=font_size,
				weight="bold", x=box_left + title_w / 2, y=center_y,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			teams_label = pyglet.text.Label(
				_slot_text(entry["red"], match.red_team_1, match.red_team_2, matches_by_batch, alliance_by_pair)
				+ "\n"
				+ _slot_text(entry["blue"], match.blue_team_1, match.blue_team_2, matches_by_batch, alliance_by_pair),
				font_name=font_name, font_size=teams_font_size, weight="bold",
				x=box_left + title_w + teams_w / 2, y=center_y, width=teams_w * 0.96,
				multiline=True, align="center", anchor_x="center", anchor_y="center", color=WHITE,
			)
			score_text = f"{max(0, match.red_score)}-{max(0, match.blue_score)}" if match.played else "-"
			score_label = pyglet.text.Label(
				score_text, font_name=font_name, font_size=font_size, weight="bold",
				x=box_left + title_w + teams_w + score_w / 2, y=center_y,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			title_label.draw()
			teams_label.draw()
			score_label.draw()

	return draw
