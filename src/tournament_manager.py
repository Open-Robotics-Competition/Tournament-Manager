import math
from pathlib import Path

import pyglet
from pyglet.font.base import Font

try:
	from . import (
		control_display_match,
		control_display_solo,
		field_display_match,
		field_display_solo,
		tournament_setup,
		generate_schedule,
		match_schedule,
		alliance_selection,
		elimination_bracket_common,
		elimination_bracket_single,
		elimination_bracket_double,
		generator_round_robin,
		generator_standard,
		analyze_schedule,
		schedule_io,
		scoring_common,
		serialInterface,
	)
except ImportError:
	import control_display_match
	import control_display_solo
	import field_display_match
	import field_display_solo
	import tournament_setup
	import generate_schedule
	import match_schedule
	import alliance_selection
	import elimination_bracket_common
	import elimination_bracket_single
	import elimination_bracket_double
	import generator_round_robin
	import generator_standard
	import analyze_schedule
	import schedule_io
	import scoring_common
	import serialInterface


Font.texture_width = 1024
Font.texture_height = 1024
pyglet.font.add_file(str(Path(__file__).resolve().parents[1] / "resources" / "freesansbold.ttf"))
FONT_NAME = "FreeSans"

CONTROL_WIDTH = 1800
CONTROL_HEIGHT = 720
CONTROL_SCALE_X = CONTROL_WIDTH / 900
CONTROL_FONT_SCALE = math.sqrt(CONTROL_SCALE_X)
WHITE = (255, 255, 255)
GOLD = (255, 204, 0)
BACKGROUND = (24, 27, 32)
TAB_INACTIVE = (65, 70, 78)
APP_ICON = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))


def build_bracket_topology(state: dict, alliance_count: int):
	if state["bracket_type"] == "double":
		return elimination_bracket_double.build_topology(alliance_count)
	return elimination_bracket_single.build_topology(alliance_count)


def create_field_display(state: dict):
	window = pyglet.window.Window(
		width=field_display_match.FIELD_WIDTH,
		height=field_display_match.FIELD_HEIGHT,
		caption="field_display",
		fullscreen=True,
	)
	window.set_icon(APP_ICON)
	match_renderer = field_display_match.create_renderer(
		window, state["modes"]["MATCH"], FONT_NAME, state
	)
	solo_renderer = field_display_solo.create_renderer(
		window, state["modes"]["SOLO"], FONT_NAME
	)
	team_list_renderer = tournament_setup.create_field_renderer(
		window, state, FONT_NAME
	)
	schedule_renderer = generate_schedule.create_field_renderer(window, FONT_NAME)
	match_schedule_renderer = match_schedule.create_field_renderer(window, state, FONT_NAME)
	alliance_selection_renderer = alliance_selection.create_field_renderer(window, state, FONT_NAME)
	elimination_bracket_renderer = elimination_bracket_common.create_field_renderer(
		window, state, FONT_NAME, lambda alliance_count: build_bracket_topology(state, alliance_count)
	)
	event_results_renderer = create_event_results_field_renderer(window, state, FONT_NAME)

	@window.event
	def on_draw():
		if state["active_mode"] == "SOLO":
			solo_renderer()
		elif state["active_mode"] == "TOURNAMENT SETUP":
			team_list_renderer()
		elif state["active_mode"] == "GENERATE SCHEDULE":
			schedule_renderer()
		elif state["active_mode"] == "MATCH SCHEDULE":
			match_schedule_renderer()
		elif state["active_mode"] == "ALLIANCE SELECTION":
			alliance_selection_renderer()
		elif state["active_mode"] == "ELIMINATION BRACKET":
			elimination_bracket_renderer()
		elif state["active_mode"] == "EVENT RESULTS":
			event_results_renderer()
		else:
			match_renderer()

	return window


def _placement_team_name(team_id, teams):
	if team_id is None or team_id < 0:
		return "TBD"
	for team in teams:
		if team.eventID == team_id:
			return team.name
	return f"Unknown team {team_id}"


def create_event_results_field_renderer(window, state: dict, font_name: str):
	width = window.width
	height = window.height
	scale_y = height / field_display_match.FIELD_HEIGHT
	background = pyglet.shapes.Rectangle(0, 0, width, height, color=(18, 20, 25))
	waiting_label = pyglet.text.Label(
		"WAITING FOR EVENT TO COMPLETE", font_name=font_name, font_size=int(48 * height / 1080),
		weight="bold", x=width / 2, y=height / 2, anchor_x="center", anchor_y="center", color=WHITE,
	)
	# Same size/position as the match field display's center logo.
	logo_size = 600 * scale_y
	logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = (width - logo_size) / 2
	logo.y = height * 0.3 - logo_size / 2

	def draw():
		window.switch_to()
		window.clear()
		background.draw()
		placements = elimination_bracket_common.get_placements(state)
		if placements is None:
			waiting_label.draw()
			return
		teams = state["teams"]
		columns = (
			("2ND PLACE", [placements["second"]], width * 0.22, height * 0.45),
			("1ST PLACE", [placements["first"]], width * 0.5, height * 0.62),
			("3RD PLACE", placements["third"], width * 0.78, height * 0.35),
		)
		for title, alliance_list, x, podium_top in columns:
			block = pyglet.shapes.Rectangle(
				x - width * 0.1, height * 0.1, width * 0.2, podium_top - height * 0.1, color=(60, 63, 68)
			)
			block.draw()
			if title == "1ST PLACE":
				logo.draw()  # in front of the center podium
			title_label = pyglet.text.Label(
				title, font_name=font_name, font_size=int(34 * height / 1080), weight="bold",
				x=x, y=height * 0.95, anchor_x="center", anchor_y="center", color=GOLD,
			)
			title_label.draw()
			body_text = "\n\n".join(
				f"{_placement_team_name(a, teams)}\n{_placement_team_name(b, teams)}"
				for a, b in alliance_list
			) or "\u2014"
			# Anchored to its bottom so the text always grows upward, clear of the podium block.
			body_label = pyglet.text.Label(
				body_text, font_name=font_name, font_size=int(22 * height / 1080), weight="bold",
				x=x, y=podium_top + height * 0.02, width=width * 0.24, multiline=True, align="center",
				anchor_x="center", anchor_y="bottom", color=WHITE,
			)
			body_label.draw()

	return draw


def create_event_results_controls(state: dict, font_name: str, window):
	scale_x = window.width / 900
	panel = pyglet.shapes.RoundedRectangle(
		40 * scale_x, 95, 820 * scale_x, 555, radius=10 * scale_x, color=BACKGROUND
	)
	text_x = 190 * scale_x  # left third of the panel
	waiting_label = pyglet.text.Label(
		"WAITING FOR EVENT TO COMPLETE", font_name=font_name, font_size=22, weight="bold",
		x=450 * scale_x, y=370, anchor_x="center", anchor_y="center", color=WHITE,
	)
	logo_region_left = 330 * scale_x
	logo_region_right = 860 * scale_x
	logo_size = min(logo_region_right - logo_region_left, 555) * 0.9
	logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = (logo_region_left + logo_region_right) / 2 - logo_size / 2
	logo.y = 95 + (555 - logo_size) / 2

	def draw():
		window.switch_to()
		panel.draw()
		placements = elimination_bracket_common.get_placements(state)
		if placements is None:
			waiting_label.draw()
			return
		logo.draw()
		teams = state["teams"]
		rows = (
			("1ST PLACE", [placements["first"]], 500),
			("2ND PLACE", [placements["second"]], 400),
			("3RD PLACE", placements["third"], 300),
		)
		for title, alliance_list, y in rows:
			title_label = pyglet.text.Label(
				title, font_name=font_name, font_size=20, weight="bold",
				x=text_x, y=y, anchor_x="center", anchor_y="center", color=GOLD,
			)
			title_label.draw()
			body_text = "   |   ".join(
				f"{_placement_team_name(a, teams)} / {_placement_team_name(b, teams)}"
				for a, b in alliance_list
			) or "\u2014"
			body_label = pyglet.text.Label(
				body_text, font_name=font_name, font_size=16,
				x=text_x, y=y - 35, anchor_x="center", anchor_y="center", color=WHITE,
			)
			body_label.draw()

	def handle_click(x, y, button, modifiers):
		return False

	def handle_scroll(x, y, scroll_x, scroll_y):
		return False

	return draw, handle_click, handle_scroll


def create_control_display(state: dict, field_window):
	window = pyglet.window.Window(
		width=CONTROL_WIDTH,
		height=CONTROL_HEIGHT,
		caption="control_display",
		resizable=False,
	)
	window.set_icon(APP_ICON)
	window.set_location(100, 100)
	background = pyglet.shapes.Rectangle(
		0, 0, CONTROL_WIDTH, CONTROL_HEIGHT, color=BACKGROUND
	)
	mode_controls = {
		"MATCH": control_display_match.create_controls(
			window, state["modes"]["MATCH"], FONT_NAME
		),
		"SOLO": control_display_solo.create_controls(
			state["modes"]["SOLO"], FONT_NAME, window
		),
	}
	setup_controls = tournament_setup.create_controls(state, FONT_NAME, window)

	def team_name_lookup(team_id):
		for team in state["teams"]:
			if team.eventID == team_id:
				return team.name
		return f"Unknown team {team_id}"

	def run_match(match):
		mode_state = state["modes"]["MATCH"]
		for team in ("red", "blue"):
			mode_state[team].update(goal=0, exc=0, p1=0, p2=0, major_foul=0, minor_foul=0)
		mode_state["timer_state"] = 0
		mode_state["timer_started_at"] = 0.0
		state["current_match"] = match
		state["current_match_source"] = "schedule"
		state["active_mode"] = "MATCH"
		window.invalid = True
		field_window.invalid = True

	def edit_match(match):
		if not match.played:
			return
		mode_state = state["modes"]["MATCH"]
		empty_breakdown = {"goal": 0, "exc": 0, "p1": 0, "p2": 0, "major_foul": 0, "minor_foul": 0}
		mode_state["red"].update(match.red_breakdown or empty_breakdown)
		mode_state["blue"].update(match.blue_breakdown or empty_breakdown)
		mode_state["timer_state"] = 2
		mode_state["timer_started_at"] = 0.0
		state["current_match"] = match
		state["current_match_source"] = "schedule"
		state["active_mode"] = "MATCH"
		window.invalid = True
		field_window.invalid = True

	def dispatch_bracket_topology(alliance_count):
		return build_bracket_topology(state, alliance_count)

	def run_bracket_match(match):
		if match.red_team_1 < 0 or match.blue_team_1 < 0:
			return
		if match.played and not elimination_bracket_common.is_most_recent_played(state, match):
			return
		mode_state = state["modes"]["MATCH"]
		for team in ("red", "blue"):
			mode_state[team].update(goal=0, exc=0, p1=0, p2=0, major_foul=0, minor_foul=0)
		mode_state["timer_state"] = 0
		mode_state["timer_started_at"] = 0.0
		state["current_match"] = match
		state["current_match_source"] = "bracket"
		state["active_mode"] = "MATCH"
		window.invalid = True
		field_window.invalid = True

	def edit_bracket_match(match):
		if not match.played or not elimination_bracket_common.is_most_recent_played(state, match):
			return
		mode_state = state["modes"]["MATCH"]
		empty_breakdown = {"goal": 0, "exc": 0, "p1": 0, "p2": 0, "major_foul": 0, "minor_foul": 0}
		mode_state["red"].update(match.red_breakdown or empty_breakdown)
		mode_state["blue"].update(match.blue_breakdown or empty_breakdown)
		mode_state["timer_state"] = 2
		mode_state["timer_started_at"] = 0.0
		state["current_match"] = match
		state["current_match_source"] = "bracket"
		state["active_mode"] = "MATCH"
		window.invalid = True
		field_window.invalid = True

	match_schedule_controls = match_schedule.create_controls(
		state, FONT_NAME, window, on_run=run_match, on_edit=edit_match
	)
	alliance_selection_controls = alliance_selection.create_controls(state, FONT_NAME, window)
	elimination_bracket_controls = elimination_bracket_common.create_controls(
		state, FONT_NAME, window, dispatch_bracket_topology,
		on_run=run_bracket_match, on_edit=edit_bracket_match,
	)
	event_results_controls = create_event_results_controls(state, FONT_NAME, window)

	def generate_round_robin_schedule():
		if state["schedule_finalized"]:
			return
		try:
			schedule = generator_round_robin.generate_round_robin(state["teams"])
			generator_round_robin.write_schedule(
				schedule, tournament_setup.tournament_data_path
			)
		except (generator_round_robin.RoundRobinError, OSError) as error:
			state["schedule_status"] = str(error)
			window.invalid = True
			return
		state["schedule"] = schedule
		statistics = analyze_schedule.analyze_schedule(schedule, state["teams"])
		state["schedule_status"] = (
			f"GENERATED ROUND-ROBIN WITH {len(schedule)} MATCHES\n"
			f"{analyze_schedule.format_schedule_statistics(statistics, state['teams'])}"
		)
		window.invalid = True

	def generate_standard_schedule(batch_count: int):
		if state["schedule_finalized"]:
			return
		try:
			schedule = generator_standard.generate_standard(state["teams"], batch_count)
			generator_standard.write_schedule(
				schedule, tournament_setup.tournament_data_path
			)
		except (generator_standard.StandardScheduleError, OSError) as error:
			state["schedule_status"] = str(error)
			window.invalid = True
			return
		state["schedule"] = schedule
		statistics = analyze_schedule.analyze_schedule(schedule, state["teams"])
		state["schedule_status"] = (
			f"GENERATED STANDARD WITH {len(schedule)} MATCHES\n"
			f"{analyze_schedule.format_schedule_statistics(statistics, state['teams'])}"
		)
		window.invalid = True

	def finalize_schedule():
		if not state["schedule"]:
			state["schedule_status"] = "GENERATE A SCHEDULE BEFORE FINALIZING"
			window.invalid = True
			return
		state["schedule_finalized"] = True
		state["active_mode"] = "MATCH SCHEDULE"
		window.invalid = True
		field_window.invalid = True

	schedule_controls = generate_schedule.create_controls(
		FONT_NAME, window, state, generate_standard_schedule,
		generate_round_robin_schedule, finalize_schedule,
	)
	tabs = {
		"TOURNAMENT SETUP": pyglet.shapes.RoundedRectangle(
			15, 674, 210, 42, radius=6, color=(166, 25, 25)
		),
		"GENERATE SCHEDULE": pyglet.shapes.RoundedRectangle(
			235, 674, 210, 42, radius=6, color=TAB_INACTIVE
		),
		"MATCH SCHEDULE": pyglet.shapes.RoundedRectangle(
			455, 674, 210, 42, radius=6, color=(45, 49, 55)
		),
		"ALLIANCE SELECTION": pyglet.shapes.RoundedRectangle(
			675, 674, 210, 42, radius=6, color=(45, 49, 55)
		),
		"ELIMINATION BRACKET": pyglet.shapes.RoundedRectangle(
			895, 674, 210, 42, radius=6, color=(45, 49, 55)
		),
		"MATCH": pyglet.shapes.RoundedRectangle(
			1115, 674, 210, 42, radius=6, color=TAB_INACTIVE
		),
		"SOLO": pyglet.shapes.RoundedRectangle(
			1335, 674, 210, 42, radius=6, color=TAB_INACTIVE
		),
		"EVENT RESULTS": pyglet.shapes.RoundedRectangle(
			1555, 674, 210, 42, radius=6, color=(45, 49, 55)
		),
	}
	tab_labels = {
		mode: pyglet.text.Label(
			mode, font_name=FONT_NAME,
			font_size=14 if mode in (
				"TOURNAMENT SETUP", "GENERATE SCHEDULE", "MATCH SCHEDULE", "ALLIANCE SELECTION",
				"ELIMINATION BRACKET", "EVENT RESULTS",
			) else 20,
			weight="bold",
			x=shape.x + shape.width / 2, y=shape.y + shape.height / 2,
			anchor_x="center", anchor_y="center", color=WHITE,
		)
		for mode, shape in tabs.items()
	}
	actions = []

	def add_action(x, text, callback, color):
		shape = pyglet.shapes.RoundedRectangle(
			x * CONTROL_SCALE_X, 70, 240 * CONTROL_SCALE_X, 68,
			radius=8 * CONTROL_SCALE_X, color=color
		)
		label = pyglet.text.Label(
			text, font_name=FONT_NAME, font_size=22 * CONTROL_FONT_SCALE, weight="bold",
			x=(x + 120) * CONTROL_SCALE_X, y=104,
			anchor_x="center", anchor_y="center", color=WHITE,
		)
		actions.append((shape, label, callback))

	def reset_controller_goals():
		controller = state["arduino"]
		if controller is None:
			return
		for mode_state in state["modes"].values():
			mode_state["red"]["goal"] = 0
			mode_state["blue"]["goal"] = 0
		try:
			controller.resetScore()
		except Exception as error:
			state["arduino"] = None
			print(f"Could not reset field controller score: {error}")

	def start_mode():
		mode_name = state["active_mode"] if state["active_mode"] in state["modes"] else "MATCH"
		mode_state = state["modes"][mode_name]
		for team in ("red", "blue"):
			mode_state[team]["goal"] = 0
		reset_controller_goals()
		mode_state["timer_state"] = 1
		mode_state["timer_started_at"] = scoring_common.start_timestamp()

	def reset_mode():
		mode_name = state["active_mode"] if state["active_mode"] in state["modes"] else "MATCH"
		mode_state = state["modes"][mode_name]
		for team in ("red", "blue"):
			mode_state[team].update(
				goal=0, exc=0, p1=0, p2=0, major_foul=0, minor_foul=0
			)
		mode_state["timer_state"] = 0
		mode_state["timer_started_at"] = 0.0
		reset_controller_goals()

	add_action(80, "START MATCH", start_mode, (42, 125, 72))
	add_action(330, "RESET MATCH", reset_mode, (150, 103, 28))

	# Offline testing only: forces the timer to 0:00 so a match can be saved without hardware.
	def end_match():
		state["modes"]["MATCH"]["timer_state"] = 2

	end_match_button = pyglet.shapes.RoundedRectangle(
		1650, 70, 140, 68, radius=8 * CONTROL_SCALE_X, color=(103, 58, 141),
	)
	end_match_label = pyglet.text.Label(
		"END\nMATCH", font_name=FONT_NAME, font_size=14 * CONTROL_FONT_SCALE, weight="bold",
		x=1720, y=104, anchor_x="center", anchor_y="center", color=WHITE,
		multiline=True, width=140, align="center",
	)

	# MATCH replaces the old quit button with back/save (below); SOLO no longer has a quit button.
	BACK_COLOR = (70, 90, 120)
	SAVE_COLOR = (42, 125, 72)
	DISABLED_COLOR = (60, 63, 68)

	back_save_button = pyglet.shapes.RoundedRectangle(
		580 * CONTROL_SCALE_X, 70, 240 * CONTROL_SCALE_X, 68,
		radius=8 * CONTROL_SCALE_X, color=BACK_COLOR,
	)
	back_save_label = pyglet.text.Label(
		"BACK", font_name=FONT_NAME, font_size=22 * CONTROL_FONT_SCALE, weight="bold",
		x=700 * CONTROL_SCALE_X, y=104, anchor_x="center", anchor_y="center", color=WHITE,
	)

	def back_save_state():
		mode_state = state["modes"]["MATCH"]
		text = "SAVE" if mode_state["timer_state"] == 2 else "BACK"
		enabled = state["current_match"] is not None and mode_state["timer_state"] != 1
		return text, enabled

	def handle_back_save():
		text, enabled = back_save_state()
		if not enabled:
			return
		match = state["current_match"]
		source = state.get("current_match_source", "schedule")
		if text == "SAVE" and match is not None:
			mode_state = state["modes"]["MATCH"]
			match.red_score = scoring_common.calc_match_score(mode_state["red"])
			match.blue_score = scoring_common.calc_match_score(mode_state["blue"])
			match.red_breakdown = dict(mode_state["red"])
			match.blue_breakdown = dict(mode_state["blue"])
			match.red_rp = scoring_common.calc_match_rp(
				mode_state["red"], match.red_score, match.blue_score
			)
			match.blue_rp = scoring_common.calc_match_rp(
				mode_state["blue"], match.blue_score, match.red_score
			)
			match.played = True
			if source == "bracket":
				elimination_bracket_common.refresh_bracket(state, dispatch_bracket_topology)
				try:
					elimination_bracket_common.write_bracket(state)
				except OSError as error:
					print(f"Could not save bracket results: {error}")
			else:
				try:
					schedule_io.write_schedule(state["schedule"], tournament_setup.tournament_data_path)
				except OSError as error:
					print(f"Could not save schedule results: {error}")
		state["current_match"] = None
		if (
			source == "bracket" and match is not None and match.match_type == "F"
			and elimination_bracket_common.get_placements(state) is not None
		):
			state["active_mode"] = "EVENT RESULTS"
		else:
			state["active_mode"] = "ELIMINATION BRACKET" if source == "bracket" else "MATCH SCHEDULE"
		window.invalid = True
		field_window.invalid = True

	# Placeholder match info for system testing; not sourced from a real schedule.
	match_info_banner = pyglet.shapes.RoundedRectangle(
		45 * CONTROL_SCALE_X, 5, 810 * CONTROL_SCALE_X, 58,
		radius=8 * CONTROL_SCALE_X, color=(38, 43, 50),
	)
	match_info_number = pyglet.text.Label(
		"Q0", font_name=FONT_NAME, font_size=22 * CONTROL_FONT_SCALE, weight="bold",
		x=120 * CONTROL_SCALE_X, y=34, anchor_x="center", anchor_y="center", color=GOLD,
	)
	match_info_red = pyglet.text.Label(
		"TEAM A   \u2022   TEAM B", font_name=FONT_NAME, font_size=18 * CONTROL_FONT_SCALE,
		weight="bold", x=320 * CONTROL_SCALE_X, y=34, anchor_x="left", anchor_y="center",
		color=(255, 130, 130),
	)
	match_info_blue = pyglet.text.Label(
		"TEAM C   \u2022   TEAM D", font_name=FONT_NAME, font_size=18 * CONTROL_FONT_SCALE,
		weight="bold", x=620 * CONTROL_SCALE_X, y=34, anchor_x="left", anchor_y="center",
		color=(140, 160, 255),
	)

	@window.event
	def on_draw():
		window.clear()
		background.draw()
		if state["active_mode"] == "TOURNAMENT SETUP":
			setup_controls[0]()
		elif state["active_mode"] == "GENERATE SCHEDULE":
			schedule_controls[0]()
		elif state["active_mode"] == "MATCH SCHEDULE":
			match_schedule_controls[0]()
		elif state["active_mode"] == "ALLIANCE SELECTION":
			alliance_selection_controls[0]()
		elif state["active_mode"] == "ELIMINATION BRACKET":
			elimination_bracket_controls[0]()
		elif state["active_mode"] == "EVENT RESULTS":
			event_results_controls[0]()
		else:
			mode_controls[state["active_mode"]][0]()
		for mode, shape in tabs.items():
			active_colors = {
				"TOURNAMENT SETUP": (166, 25, 25),
				"MATCH": (166, 25, 25),
				"SOLO": (26, 30, 171),
				"GENERATE SCHEDULE": (48, 118, 77),
				"MATCH SCHEDULE": (54, 104, 151),
				"ALLIANCE SELECTION": (103, 58, 141),
				"ELIMINATION BRACKET": (150, 103, 28),
				"EVENT RESULTS": (48, 118, 77),
			}
			if mode == "GENERATE SCHEDULE" and state["schedule_finalized"]:
				shape.color = (45, 49, 55)
			elif mode == "MATCH SCHEDULE" and not state["schedule_finalized"]:
				shape.color = (45, 49, 55)
			elif mode == "ALLIANCE SELECTION" and not alliance_selection.all_matches_played(state):
				shape.color = (45, 49, 55)
			elif mode == "ELIMINATION BRACKET" and state["bracket_type"] is None:
				shape.color = (45, 49, 55)
			else:
				shape.color = active_colors[mode] if state["active_mode"] == mode else TAB_INACTIVE
			shape.draw()
			tab_labels[mode].draw()
		if state["active_mode"] in mode_controls:
			for shape, label, _callback in actions:
				shape.draw()
				label.text = (
					f"START {state['active_mode']}" if label.text.startswith("START") else
					f"RESET {state['active_mode']}" if label.text.startswith("RESET") else label.text
				)
				label.draw()
		if state["active_mode"] == "MATCH":
			match = state["current_match"]
			if match is None:
				match_info_number.text = "Q0"
				match_info_red.text = "TEAM A   \u2022   TEAM B"
				match_info_blue.text = "TEAM C   \u2022   TEAM D"
			else:
				match_info_number.text = f"{match.match_type}{match.match_number}"
				match_info_red.text = (
					f"{team_name_lookup(match.red_team_1)}   \u2022   {team_name_lookup(match.red_team_2)}"
				)
				match_info_blue.text = (
					f"{team_name_lookup(match.blue_team_1)}   \u2022   {team_name_lookup(match.blue_team_2)}"
				)
			match_info_banner.draw()
			match_info_number.draw()
			match_info_red.draw()
			match_info_blue.draw()

			text, enabled = back_save_state()
			back_save_label.text = text
			back_save_button.color = (
				(SAVE_COLOR if text == "SAVE" else BACK_COLOR) if enabled else DISABLED_COLOR
			)
			back_save_button.draw()
			back_save_label.draw()
			if state["arduino"] is None:
				end_match_button.draw()
				end_match_label.draw()

	@window.event
	def on_close():
		if field_window.context is not None:
			field_window.close()
		pyglet.app.exit()

	@window.event
	def on_mouse_press(x, y, button, modifiers):
		if button != pyglet.window.mouse.LEFT:
			return
		for mode, shape in tabs.items():
			if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
				if mode == "MATCH SCHEDULE" and not state["schedule_finalized"]:
					return
				if mode == "GENERATE SCHEDULE" and state["schedule_finalized"]:
					return
				if mode == "ALLIANCE SELECTION" and not alliance_selection.all_matches_played(state):
					return
				if mode == "ELIMINATION BRACKET" and state["bracket_type"] is None:
					return
				if mode == "MATCH":
					state["current_match"] = None
				state["active_mode"] = mode
				window.invalid = True
				field_window.invalid = True
				return
		if state["active_mode"] == "TOURNAMENT SETUP":
			if setup_controls[1](x, y, button, modifiers):
				window.invalid = True
				field_window.invalid = True
				return
		elif state["active_mode"] == "GENERATE SCHEDULE":
			if schedule_controls[1](x, y):
				window.invalid = True
				field_window.invalid = True
				return
		elif state["active_mode"] == "MATCH SCHEDULE":
			if match_schedule_controls[1](x, y, button, modifiers):
				window.invalid = True
				return
		elif state["active_mode"] == "ALLIANCE SELECTION":
			if alliance_selection_controls[1](x, y, button, modifiers):
				window.invalid = True
				return
		elif state["active_mode"] == "ELIMINATION BRACKET":
			if elimination_bracket_controls[1](x, y, button, modifiers):
				window.invalid = True
				return
		elif state["active_mode"] == "EVENT RESULTS":
			if event_results_controls[1](x, y, button, modifiers):
				window.invalid = True
				return
		elif mode_controls[state["active_mode"]][1](x, y):
			window.invalid = True
			field_window.invalid = True
			return
		if state["active_mode"] in mode_controls:
			for shape, _label, callback in reversed(actions):
				if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
					callback()
					window.invalid = True
					field_window.invalid = True
					return
		if state["active_mode"] == "MATCH":
			_text, enabled = back_save_state()
			if (
				enabled
				and back_save_button.x <= x <= back_save_button.x + back_save_button.width
				and back_save_button.y <= y <= back_save_button.y + back_save_button.height
			):
				handle_back_save()
				window.invalid = True
				field_window.invalid = True
				return
			if (
				state["arduino"] is None
				and end_match_button.x <= x <= end_match_button.x + end_match_button.width
				and end_match_button.y <= y <= end_match_button.y + end_match_button.height
			):
				end_match()
				window.invalid = True
				field_window.invalid = True
				return

	@window.event
	def on_text(text):
		if state["active_mode"] == "TOURNAMENT SETUP":
			setup_controls[2](text)
			window.invalid = True
		elif state["active_mode"] == "GENERATE SCHEDULE":
			schedule_controls[2](text)
			window.invalid = True

	@window.event
	def on_text_motion(motion):
		if state["active_mode"] == "TOURNAMENT SETUP":
			setup_controls[3](motion)
			window.invalid = True
		elif state["active_mode"] == "GENERATE SCHEDULE":
			schedule_controls[3](motion)
			window.invalid = True

	@window.event
	def on_key_press(symbol, modifiers):
		if state["active_mode"] == "TOURNAMENT SETUP":
			setup_controls[4](symbol, modifiers)
			window.invalid = True
		elif state["active_mode"] == "GENERATE SCHEDULE":
			schedule_controls[4](symbol, modifiers)
			window.invalid = True

	@window.event
	def on_mouse_scroll(x, y, scroll_x, scroll_y):
		if state["active_mode"] == "MATCH SCHEDULE":
			if match_schedule_controls[2](x, y, scroll_x, scroll_y):
				window.invalid = True
		elif state["active_mode"] == "ALLIANCE SELECTION":
			if alliance_selection_controls[2](x, y, scroll_x, scroll_y):
				window.invalid = True
		elif state["active_mode"] == "ELIMINATION BRACKET":
			if elimination_bracket_controls[2](x, y, scroll_x, scroll_y):
				window.invalid = True

	return window


def create_initial_state() -> dict:
	def new_mode_state():
		return {
			"red": {
				"goal": 0, "exc": 0, "p1": 0, "p2": 0,
				"major_foul": 0, "minor_foul": 0,
			},
			"blue": {
				"goal": 0, "exc": 0, "p1": 0, "p2": 0,
				"major_foul": 0, "minor_foul": 0,
			},
			"timer_state": 0,
			"timer_started_at": 0.0,
		}

	return {
		"active_mode": "TOURNAMENT SETUP",
		"modes": {"MATCH": new_mode_state(), "SOLO": new_mode_state()},
		"arduino": None,
		"teams": [],
		"team_list_revision": 0,
		"schedule": [],
		"schedule_status": "",
		"schedule_finalized": False,
		"current_match": None,
		"current_match_source": "schedule",
		"alliance_state": {
			"team_status": {},
			"accept_order": [],
			"alliances": [[None, None] for _ in range(8)],
		},
		"bracket_type": None,
		"bracket": [],
	}


def main() -> None:
	state = create_initial_state()
	try:
		arduino = serialInterface.ArduinoInterface()
		print("Field controller connected")
	except Exception as error:
		arduino = None
		print(f"Field controller not connected, using manual goal controls: {error}")
	state["arduino"] = arduino

	field_window = create_field_display(state)
	control_window = create_control_display(state, field_window)

	def refresh_windows(_delta_time):
		if state["arduino"] is not None:
			mode_name = state["active_mode"] if state["active_mode"] in state["modes"] else "MATCH"
			mode_state = state["modes"][mode_name]
			try:
				red_goals, blue_goals = state["arduino"].updateGoals(
					mode_state["red"]["goal"], mode_state["blue"]["goal"]
				)
			except Exception as error:
				print(f"Field controller disconnected; using manual goal controls: {error}")
				state["arduino"] = None
			else:
				mode_state["red"]["goal"] = red_goals
				mode_state["blue"]["goal"] = blue_goals
		control_window.invalid = True
		field_window.invalid = True

	pyglet.clock.schedule_interval(refresh_windows, 1 / 15)
	pyglet.app.run()


if __name__ == "__main__":
	main()