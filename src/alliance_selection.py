import csv
from pathlib import Path

import pyglet

try:
	from . import calculate_rankings, tournament_setup
	from . import elimination_bracket_common as bracket_common
	from . import elimination_bracket_single, elimination_bracket_double
except ImportError:
	import calculate_rankings
	import tournament_setup
	import elimination_bracket_common as bracket_common
	import elimination_bracket_single
	import elimination_bracket_double

WHITE = (255, 255, 255)
PANEL = (38, 43, 50)
ROW_A = (45, 51, 59)
ROW_B = (35, 40, 47)
GOLD = (255, 204, 0)
BUTTON_ACCEPT = (48, 118, 77)
BUTTON_DECLINE = (150, 103, 28)
BUTTON_DROP = (145, 45, 45)
BUTTON_DISABLED = (55, 58, 62)
ALLIANCES_FILENAME = "alliances.txt"


def all_matches_played(state: dict) -> bool:
	schedule = state["schedule"]
	return bool(schedule) and all(match.played for match in schedule)


def _team_name(team_id, teams):
	for team in teams:
		if team.eventID == team_id:
			return team.name
	return f"Unknown team {team_id}"


def recompute_alliances(state: dict) -> None:
	alliance_state = state["alliance_state"]
	team_status = alliance_state["team_status"]
	accept_queue = list(alliance_state["accept_order"])
	ranked_teams = [entry["team"] for entry in calculate_rankings.calculate_rankings(state["schedule"], state["teams"])]

	dropped = {team_id for team_id, status in team_status.items() if status == "dropped"}
	placed = set()
	alliances = [[None, None] for _ in range(8)]

	alliance_index = 0
	while alliance_index < 8:
		captain = next(
			(team for team in ranked_teams if team.eventID not in dropped and team.eventID not in placed), None
		)
		if captain is None:
			break
		alliances[alliance_index][0] = captain.eventID
		placed.add(captain.eventID)

		partner_id = None
		while accept_queue:
			candidate_id = accept_queue.pop(0)
			if candidate_id in dropped or candidate_id in placed:
				continue
			partner_id = candidate_id
			break
		if partner_id is not None:
			alliances[alliance_index][1] = partner_id
			placed.add(partner_id)
			alliance_index += 1
			continue

		remaining_eligible = [
			team for team in ranked_teams if team.eventID not in dropped and team.eventID not in placed
		]
		remaining_pending = [
			team for team in remaining_eligible if team_status.get(team.eventID, "pending") == "pending"
		]
		if not remaining_pending and remaining_eligible:
			for fill_index in range(alliance_index, 8):
				for slot in range(2):
					if alliances[fill_index][slot] is not None:
						continue
					next_team = next(
						(team for team in remaining_eligible if team.eventID not in placed), None
					)
					if next_team is None:
						break
					alliances[fill_index][slot] = next_team.eventID
					placed.add(next_team.eventID)
			break
		break

	alliance_state["alliances"] = alliances
	for alliance in alliances:
		for team_id in alliance:
			if team_id is not None:
				team_status[team_id] = "in_alliance"


def alliances_full(state: dict) -> bool:
	"""True once every alliance slot is filled, regardless of any still-pending teams left over."""
	return all(
		team_1 is not None and team_2 is not None
		for team_1, team_2 in state["alliance_state"]["alliances"]
	)


def stuck_captain_id(state: dict):
	"""Team stuck alone as a captain with no remaining teams left to pair with."""
	alliance_state = state["alliance_state"]
	team_status = alliance_state["team_status"]
	captain_id = None
	for alliance in alliance_state["alliances"]:
		if alliance[0] is not None and alliance[1] is None:
			captain_id = alliance[0]
	if captain_id is None:
		return None
	for team in state["teams"]:
		if team.eventID == captain_id:
			continue
		if team_status.get(team.eventID, "pending") not in ("in_alliance", "dropped"):
			return None
	return captain_id


def create_controls(state: dict, font_name: str, window):
	scale_x = window.width / 900
	panel = pyglet.shapes.RoundedRectangle(
		40 * scale_x, 95, 820 * scale_x, 555, radius=10 * scale_x, color=PANEL
	)
	heading = pyglet.text.Label(
		"ALLIANCE SELECTION", font_name=font_name, font_size=30, weight="bold",
		x=450 * scale_x, y=620, anchor_x="center", anchor_y="center", color=WHITE,
	)
	alliances_heading = pyglet.text.Label(
		"ALLIANCES", font_name=font_name, font_size=20, weight="bold",
		x=195 * scale_x, y=580, anchor_x="center", anchor_y="center", color=WHITE,
	)
	teams_heading = pyglet.text.Label(
		"TEAMS", font_name=font_name, font_size=20, weight="bold",
		x=610 * scale_x, y=580, anchor_x="center", anchor_y="center", color=WHITE,
	)
	divider = pyglet.shapes.Line(
		350 * scale_x, 140, 350 * scale_x, 560, thickness=2, color=(70, 74, 80),
	)

	alliance_row_top = 555
	alliance_row_height = 52.5
	alliance_rows = []
	for index in range(8):
		row_y = alliance_row_top - index * alliance_row_height - alliance_row_height
		background = pyglet.shapes.Rectangle(
			55 * scale_x, row_y, 280 * scale_x, alliance_row_height - 4,
			color=ROW_A if index % 2 == 0 else ROW_B,
		)
		label = pyglet.text.Label(
			f"A{index + 1}: \u2014", font_name=font_name, font_size=14, weight="bold",
			x=65 * scale_x, y=row_y + alliance_row_height / 2 - 2,
			width=260 * scale_x, anchor_x="left", anchor_y="center", color=WHITE,
		)
		alliance_rows.append((background, label))

	viewport_bottom = 145
	viewport_top = 550
	row_height = 76
	visible_rows = 5
	scroll_offset = 0
	rows = []
	last_signature = None

	def ensure_initialized():
		alliance_state = state["alliance_state"]
		if alliance_state.get("initialized"):
			return
		if not all_matches_played(state):
			return
		recompute_alliances(state)
		alliance_state["initialized"] = True

	def handle_accept(team_id):
		alliance_state = state["alliance_state"]
		if alliances_full(state) or alliance_state["team_status"].get(team_id, "pending") != "pending":
			return
		alliance_state["accept_order"].append(team_id)
		recompute_alliances(state)

	def handle_decline(team_id):
		alliance_state = state["alliance_state"]
		if alliances_full(state) or alliance_state["team_status"].get(team_id, "pending") != "pending":
			return
		alliance_state["team_status"][team_id] = "declined"
		recompute_alliances(state)

	def handle_drop(team_id):
		alliance_state = state["alliance_state"]
		if alliances_full(state):
			return
		if (
			alliance_state["team_status"].get(team_id, "pending") == "in_alliance"
			and team_id != stuck_captain_id(state)
		):
			return
		alliance_state["team_status"][team_id] = "dropped"
		recompute_alliances(state)

	def selection_complete():
		if alliances_full(state):
			return True
		alliance_state = state["alliance_state"]
		team_status = alliance_state["team_status"]
		for team in state["teams"]:
			status = team_status.get(team.eventID, "pending")
			if status not in ("in_alliance", "dropped"):
				return False
		return True

	def finalize_alliances():
		if not selection_complete():
			return
		output_path = Path(tournament_setup.tournament_data_path) / ALLIANCES_FILENAME
		output_path.parent.mkdir(parents=True, exist_ok=True)
		with output_path.open("w", newline="", encoding="utf-8") as alliances_file:
			writer = csv.writer(alliances_file)
			writer.writerow(("alliance", "team_1", "team_2"))
			for index, alliance in enumerate(state["alliance_state"]["alliances"], start=1):
				writer.writerow((index, alliance[0], alliance[1]))
		state["alliance_state"]["finalized"] = True

	def load_alliances():
		input_path = Path(tournament_setup.tournament_data_path) / ALLIANCES_FILENAME
		if not input_path.exists():
			return
		try:
			with input_path.open("r", newline="", encoding="utf-8") as alliances_file:
				reader = csv.DictReader(alliances_file)
				loaded = [[None, None] for _ in range(8)]
				for row in reader:
					index = int(row["alliance"]) - 1
					if not (0 <= index < 8):
						continue
					team_1 = row["team_1"]
					team_2 = row["team_2"]
					loaded[index][0] = int(team_1) if team_1 else None
					loaded[index][1] = int(team_2) if team_2 else None
		except (OSError, ValueError, KeyError):
			return
		alliance_state = state["alliance_state"]
		alliance_state["alliances"] = loaded
		for alliance in loaded:
			for team_id in alliance:
				if team_id is not None:
					alliance_state["team_status"][team_id] = "in_alliance"

	def alliances_file_available():
		return (Path(tournament_setup.tournament_data_path) / ALLIANCES_FILENAME).exists()

	def elimination_ready():
		return (
			state["alliance_state"].get("finalized", False)
			and not state["alliance_state"].get("elimination_started", False)
		)

	def start_elimination(bracket_module):
		if not elimination_ready():
			return
		bracket_module.generate_bracket(state)
		bracket_common.write_bracket(state)
		state["alliance_state"]["elimination_started"] = True
		state["active_mode"] = "ELIMINATION BRACKET"

	finalize_button = pyglet.shapes.RoundedRectangle(
		45 * scale_x, 70, 185 * scale_x, 58, radius=8 * scale_x, color=BUTTON_ACCEPT,
	)
	finalize_label = pyglet.text.Label(
		"FINALIZE\nALLIANCES", font_name=font_name, font_size=12, weight="bold",
		x=137.5 * scale_x, y=99, width=185 * scale_x, multiline=True, align="center",
		anchor_x="center", anchor_y="center", color=WHITE,
	)
	load_button = pyglet.shapes.RoundedRectangle(
		240 * scale_x, 70, 185 * scale_x, 58, radius=8 * scale_x, color=(54, 104, 151),
	)
	load_label = pyglet.text.Label(
		"LOAD\nALLIANCES", font_name=font_name, font_size=12, weight="bold",
		x=332.5 * scale_x, y=99, width=185 * scale_x, multiline=True, align="center",
		anchor_x="center", anchor_y="center", color=WHITE,
	)
	start_single_button = pyglet.shapes.RoundedRectangle(
		435 * scale_x, 70, 185 * scale_x, 58, radius=8 * scale_x, color=(103, 58, 141),
	)
	start_single_label = pyglet.text.Label(
		"START SINGLE ELIM", font_name=font_name, font_size=11, weight="bold",
		x=527.5 * scale_x, y=99, width=185 * scale_x, multiline=True, align="center",
		anchor_x="center", anchor_y="center", color=WHITE,
	)
	start_double_button = pyglet.shapes.RoundedRectangle(
		630 * scale_x, 70, 185 * scale_x, 58, radius=8 * scale_x, color=(103, 58, 141),
	)
	start_double_label = pyglet.text.Label(
		"START DOUBLE ELIM", font_name=font_name, font_size=11, weight="bold",
		x=722.5 * scale_x, y=99, width=185 * scale_x, multiline=True, align="center",
		anchor_x="center", anchor_y="center", color=WHITE,
	)

	def refresh_rows():
		nonlocal rows, last_signature
		rankings = calculate_rankings.calculate_rankings(state["schedule"], state["teams"])
		alliance_state = state["alliance_state"]
		signature = (
			tuple((entry["team"].eventID, entry["rank"]) for entry in rankings),
			tuple(sorted(alliance_state["team_status"].items())),
		)
		if signature == last_signature:
			return
		last_signature = signature
		rows = []
		for index, entry in enumerate(rankings):
			team = entry["team"]
			y = viewport_top - index * row_height - row_height
			background = pyglet.shapes.Rectangle(
				370 * scale_x, y, 480 * scale_x, row_height - 5,
				color=ROW_A if index % 2 == 0 else ROW_B,
			)
			name_label = pyglet.text.Label(
				f"#{entry['rank']}  {team.name}", font_name=font_name, font_size=16,
				weight="bold", x=380 * scale_x, y=y + 35,
				width=140 * scale_x, anchor_x="left", anchor_y="center", color=WHITE,
			)
			accept_button = pyglet.shapes.RoundedRectangle(
				525 * scale_x, y + 13, 100 * scale_x, 44, radius=5, color=BUTTON_ACCEPT,
			)
			accept_label = pyglet.text.Label(
				"ACCEPT", font_name=font_name, font_size=12, weight="bold",
				x=575 * scale_x, y=y + 35, anchor_x="center", anchor_y="center", color=WHITE,
			)
			decline_button = pyglet.shapes.RoundedRectangle(
				635 * scale_x, y + 13, 100 * scale_x, 44, radius=5, color=BUTTON_DECLINE,
			)
			decline_label = pyglet.text.Label(
				"DECLINE", font_name=font_name, font_size=12, weight="bold",
				x=685 * scale_x, y=y + 35, anchor_x="center", anchor_y="center", color=WHITE,
			)
			drop_button = pyglet.shapes.RoundedRectangle(
				745 * scale_x, y + 13, 80 * scale_x, 44, radius=5, color=BUTTON_DROP,
			)
			drop_label = pyglet.text.Label(
				"DROP", font_name=font_name, font_size=12, weight="bold",
				x=785 * scale_x, y=y + 35, anchor_x="center", anchor_y="center", color=WHITE,
			)
			rows.append((
				team.eventID, background, name_label,
				accept_button, accept_label, decline_button, decline_label, drop_button, drop_label,
			))

	def draw():
		window.switch_to()
		window.clear()
		ensure_initialized()
		panel.draw()
		heading.draw()
		alliances_heading.draw()
		teams_heading.draw()
		divider.draw()

		alliance_state = state["alliance_state"]
		for index, (background, label) in enumerate(alliance_rows):
			background.draw()
			slot_1, slot_2 = alliance_state["alliances"][index]
			name_1 = _team_name(slot_1, state["teams"]) if slot_1 is not None else "\u2014"
			name_2 = _team_name(slot_2, state["teams"]) if slot_2 is not None else "\u2014"
			label.text = f"A{index + 1}: {name_1} / {name_2}"
			label.draw()

		refresh_rows()
		max_offset = max(0, len(rows) - visible_rows)
		first_row = min(scroll_offset, max_offset)
		vertical_shift = first_row * row_height
		stuck_id = stuck_captain_id(state)
		full = alliances_full(state)
		for row in rows[first_row:first_row + visible_rows]:
			team_id, background, name_label, accept_button, accept_label, \
				decline_button, decline_label, drop_button, drop_label = row
			status = alliance_state["team_status"].get(team_id, "pending")
			accept_button.color = BUTTON_ACCEPT if status == "pending" and not full else BUTTON_DISABLED
			decline_button.color = BUTTON_DECLINE if status == "pending" and not full else BUTTON_DISABLED
			drop_enabled = (status not in ("in_alliance", "dropped") or team_id == stuck_id) and not full
			drop_button.color = BUTTON_DROP if drop_enabled else BUTTON_DISABLED
			for element in (
				background, name_label, accept_button, accept_label,
				decline_button, decline_label, drop_button, drop_label,
			):
				element.y += vertical_shift
				element.draw()
				element.y -= vertical_shift

		finalize_button.color = BUTTON_ACCEPT if selection_complete() else BUTTON_DISABLED
		finalize_button.draw()
		finalize_label.draw()
		load_button.color = (54, 104, 151) if alliances_file_available() else BUTTON_DISABLED
		load_button.draw()
		load_label.draw()

		ready = elimination_ready()
		alliance_lookup = bracket_common.get_alliance_lookup(state)
		start_single_button.color = (103, 58, 141) if ready else BUTTON_DISABLED
		start_single_label.text = f"START SINGLE\nELIM ({elimination_bracket_single.match_count(alliance_lookup)})"
		start_single_button.draw()
		start_single_label.draw()
		start_double_button.color = (103, 58, 141) if ready else BUTTON_DISABLED
		start_double_label.text = f"START DOUBLE\nELIM ({elimination_bracket_double.match_count(alliance_lookup)})"
		start_double_button.draw()
		start_double_label.draw()

	def handle_click(x, y, button, modifiers):
		max_offset = max(0, len(rows) - visible_rows)
		first_row = min(scroll_offset, max_offset)
		vertical_shift = first_row * row_height
		alliance_state = state["alliance_state"]
		stuck_id = stuck_captain_id(state)
		full = alliances_full(state)
		for row in rows[first_row:first_row + visible_rows]:
			team_id, _background, _name_label, accept_button, _accept_label, \
				decline_button, _decline_label, drop_button, _drop_label = row
			status = alliance_state["team_status"].get(team_id, "pending")
			if (
				status == "pending" and not full
				and accept_button.x <= x <= accept_button.x + accept_button.width
				and accept_button.y + vertical_shift <= y <= accept_button.y + vertical_shift + accept_button.height
			):
				handle_accept(team_id)
				return True
			if (
				status == "pending" and not full
				and decline_button.x <= x <= decline_button.x + decline_button.width
				and decline_button.y + vertical_shift <= y <= decline_button.y + vertical_shift + decline_button.height
			):
				handle_decline(team_id)
				return True
			if (
				(status not in ("in_alliance", "dropped") or team_id == stuck_id) and not full
				and drop_button.x <= x <= drop_button.x + drop_button.width
				and drop_button.y + vertical_shift <= y <= drop_button.y + vertical_shift + drop_button.height
			):
				handle_drop(team_id)
				return True
		if (
			selection_complete()
			and finalize_button.x <= x <= finalize_button.x + finalize_button.width
			and finalize_button.y <= y <= finalize_button.y + finalize_button.height
		):
			finalize_alliances()
			return True
		if (
			alliances_file_available()
			and load_button.x <= x <= load_button.x + load_button.width
			and load_button.y <= y <= load_button.y + load_button.height
		):
			load_alliances()
			return True
		if (
			elimination_ready()
			and start_single_button.x <= x <= start_single_button.x + start_single_button.width
			and start_single_button.y <= y <= start_single_button.y + start_single_button.height
		):
			start_elimination(elimination_bracket_single)
			return True
		if (
			elimination_ready()
			and start_double_button.x <= x <= start_double_button.x + start_double_button.width
			and start_double_button.y <= y <= start_double_button.y + start_double_button.height
		):
			start_elimination(elimination_bracket_double)
			return True
		return False

	def handle_scroll(x, y, scroll_x, scroll_y):
		nonlocal scroll_offset
		max_offset = max(0, len(rows) - visible_rows)
		scroll_offset = min(max(0, scroll_offset - int(scroll_y)), max_offset)
		return True

	return draw, handle_click, handle_scroll


def create_field_renderer(window, state: dict, font_name: str):
	width = window.width
	height = window.height
	background = pyglet.shapes.Rectangle(0, 0, width, height, color=(18, 20, 25))
	divider_x = width * 0.4
	divider = pyglet.shapes.Line(
		divider_x, height * 0.04, divider_x, height * 0.9, thickness=3, color=(70, 74, 80),
	)
	alliances_heading = pyglet.text.Label(
		"ALLIANCES", font_name=font_name, font_size=int(42 * height / 1080), weight="bold",
		x=divider_x / 2, y=height * 0.93, anchor_x="center", anchor_y="center", color=WHITE,
	)

	alliance_row_height = height * 0.10
	alliance_viewport_top = height * 0.85

	teams_left = divider_x + width * 0.02
	teams_right_full = width * 0.98
	teams_viewport_top = height * 0.85
	teams_viewport_bottom = height * 0.05
	target_row_height = height * 0.038

	# The logo sits on the right of the teams panel, sized as large as it can be without
	# overlapping a 25-character team name rendered at the list's largest (single-column) font.
	probe_font_size = max(10, int(20 * height / 1080))
	name_probe_width = pyglet.text.Label(
		"A" * 25, font_name=font_name, font_size=probe_font_size, weight="bold",
	).content_width
	min_text_zone_w = name_probe_width + width * 0.02
	logo_gap = width * 0.015
	logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	logo_size = max(0.0, min(
		teams_viewport_top - teams_viewport_bottom,
		(teams_right_full - teams_left) - min_text_zone_w - logo_gap,
	))
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = teams_right_full - logo_size
	logo.y = teams_viewport_top - logo_size

	teams_right = teams_right_full - logo_size - logo_gap
	teams_heading = pyglet.text.Label(
		"TEAMS", font_name=font_name, font_size=int(42 * height / 1080), weight="bold",
		x=(teams_left + teams_right) / 2, y=height * 0.93, anchor_x="center", anchor_y="center", color=WHITE,
	)

	team_rows = []
	last_team_signature = None

	def refresh_team_rows():
		nonlocal team_rows, last_team_signature
		rankings = calculate_rankings.calculate_rankings(state["schedule"], state["teams"])
		team_status = state["alliance_state"]["team_status"]
		signature = (
			tuple((entry["team"].eventID, entry["rank"]) for entry in rankings),
			tuple(sorted(team_status.items())),
		)
		if signature == last_team_signature:
			return
		last_team_signature = signature

		team_count = len(rankings)
		available_height = teams_viewport_top - teams_viewport_bottom
		rows_per_column = max(1, int(available_height / target_row_height))
		columns = max(1, -(-team_count // rows_per_column))
		row_height = available_height / rows_per_column
		column_width = (teams_right - teams_left) / columns
		font_size = max(10, int(20 * height / 1080 * min(1.0, 6 / max(1, columns))))

		team_rows = []
		for index, entry in enumerate(rankings):
			column = index // rows_per_column
			row = index % rows_per_column
			x = teams_left + column * column_width + 10
			y = teams_viewport_top - row * row_height
			team = entry["team"]
			status = team_status.get(team.eventID, "pending")
			label = pyglet.text.Label(
				f"#{entry['rank']} {team.name}", font_name=font_name, font_size=font_size,
				weight="bold", x=x, y=y, anchor_x="left", anchor_y="center", color=WHITE,
			)
			strike_line = pyglet.shapes.Line(x, y, x, y, thickness=2, color=(200, 60, 60))
			team_rows.append((label, strike_line, status != "pending"))

	def draw():
		window.switch_to()
		window.clear()
		background.draw()
		alliances_heading.draw()
		teams_heading.draw()
		divider.draw()
		logo.draw()

		alliance_state = state["alliance_state"]
		alliance_title_w = divider_x * 0.28
		teams_zone_w = divider_x - alliance_title_w
		for index, (slot_1, slot_2) in enumerate(alliance_state["alliances"]):
			y = alliance_viewport_top - index * alliance_row_height
			name_1 = _team_name(slot_1, state["teams"]) if slot_1 is not None else "\u2014"
			name_2 = _team_name(slot_2, state["teams"]) if slot_2 is not None else "\u2014"
			title_label = pyglet.text.Label(
				f"ALLIANCE {index + 1}", font_name=font_name, font_size=int(22 * height / 1080),
				weight="bold", x=alliance_title_w / 2, y=y,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			teams_label = pyglet.text.Label(
				f"{name_1}\n{name_2}", font_name=font_name, font_size=int(20 * height / 1080),
				weight="bold", x=alliance_title_w + teams_zone_w / 2, y=y, width=teams_zone_w * 0.95,
				multiline=True, align="center", anchor_x="center", anchor_y="center", color=WHITE,
			)
			title_label.draw()
			teams_label.draw()

		refresh_team_rows()
		for label, strike_line, crossed_out in team_rows:
			label.draw()
			if crossed_out:
				strike_line.x = label.x
				strike_line.y = label.y
				strike_line.x2 = label.x + label.content_width
				strike_line.y2 = label.y
				strike_line.draw()

	return draw
