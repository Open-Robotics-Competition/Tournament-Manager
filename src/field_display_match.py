from pathlib import Path

import pyglet

try:
	from .scoring_common import (
		GOAL_RP_THRESHOLD, PARK_RP_THRESHOLD, calc_match_score,
		goal_points, parking_points, timer_text,
	)
except ImportError:
	from scoring_common import (
		GOAL_RP_THRESHOLD, PARK_RP_THRESHOLD, calc_match_score,
		goal_points, parking_points, timer_text,
	)

RED = (166, 25, 25)
BLUE = (26, 30, 171)
GOLD = (255, 204, 0)
WHITE = (255, 255, 255)
RP_GREY = (90, 93, 98)
FIELD_WIDTH = 1920
FIELD_HEIGHT = 1080
TIMER_SECONDS = 120


def create_renderer(window, state: dict, font_name: str, app_state: dict | None = None):
	width = window.width
	height = window.height
	scale_x = width / FIELD_WIDTH
	scale_y = height / FIELD_HEIGHT
	radius = 30 * min(scale_x, scale_y)
	border = 15 * min(scale_x, scale_y)

	red_panel = pyglet.shapes.Rectangle(0, 0, width / 2 - 50 * scale_x, height, color=RED)
	blue_panel = pyglet.shapes.Rectangle(
		width / 2 + 50 * scale_x, 0, width / 2 - 50 * scale_x, height, color=BLUE
	)
	timer_frame = pyglet.shapes.RoundedRectangle(
		width * 0.25, height * 0.59, width * 0.5, height * 0.34,
		radius=radius, color=GOLD,
	)
	timer_face = pyglet.shapes.RoundedRectangle(
		width * 0.25 + border, height * 0.59 + border,
		width * 0.5 - 2 * border, height * 0.34 - 2 * border,
		radius=radius - border, color=(0, 0, 0),
	)
	logo_path = Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"
	logo_image = pyglet.image.load(str(logo_path))
	logo_size = 600 * scale_y
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = (width - logo_size) / 2
	logo.y = height * 0.3 - logo_size / 2

	score_font_size = int(height / 4 * 0.75)
	subscore_font_size = int(height / 16 * 0.75)
	red_label = pyglet.text.Label(
		"0", font_name=font_name, font_size=score_font_size, weight="bold",
		color=WHITE, anchor_x="center", anchor_y="center",
	)
	blue_label = pyglet.text.Label(
		"0", font_name=font_name, font_size=score_font_size, weight="bold",
		color=WHITE, anchor_x="center", anchor_y="center",
	)
	timer_label = pyglet.text.Label(
		"2:00", font_name=font_name, font_size=int(height / 3 * 0.75), weight="bold",
		color=WHITE, anchor_x="center", anchor_y="center",
	)
	# Placeholder match info for system testing; not sourced from a real schedule.
	match_number_label = pyglet.text.Label(
		"Q0", font_name=font_name, font_size=int(height / 16), weight="bold",
		color=WHITE, x=width * 0.02, y=height * 0.97,
		anchor_x="left", anchor_y="top",
	)
	red_teams_label = pyglet.text.Label(
		"TEAM A\nTEAM B", font_name=font_name, font_size=int(height / 32), weight="bold",
		color=WHITE, x=width * 0.125, y=height * 0.775,
		multiline=True, width=width * 0.2, align="center",
		anchor_x="center", anchor_y="center",
	)
	blue_teams_label = pyglet.text.Label(
		"TEAM C\nTEAM D", font_name=font_name, font_size=int(height / 32), weight="bold",
		color=WHITE, x=width * 0.875, y=height * 0.775,
		multiline=True, width=width * 0.2, align="center",
		anchor_x="center", anchor_y="center",
	)
	subscore_labels = []
	for team_key, team_x in (("red", width * 0.2), ("blue", width * 0.8)):
		for score_key, title, top_fraction in (
			("goal", "GOAL", 0.75),
			("exc", "EXCL", 0.8),
			("p1", "PRK1", 0.85),
			("p2", "PRK2", 0.9),
			("foul", "FOUL", 0.95),
		):
			label = pyglet.text.Label(
				"", font_name=font_name, font_size=subscore_font_size, weight="bold",
				color=WHITE, x=team_x, y=height * (1 - top_fraction),
				anchor_x="center", anchor_y="center",
			)
			subscore_labels.append((label, team_key, score_key, title))

	rp_box_width = width * 0.085
	rp_box_height = height * 0.05
	rp_box_gap = width * 0.01
	rp_boxes = []
	for team_key, team_x in (("red", width * 0.2), ("blue", width * 0.8)):
		total_width = rp_box_width * 2 + rp_box_gap
		start_x = team_x - total_width / 2
		for index, (kind, title) in enumerate((("goal", "GOAL RP"), ("park", "PARK RP"))):
			box_x = start_x + index * (rp_box_width + rp_box_gap)
			box_y = height * 0.55 - rp_box_height / 2
			shape = pyglet.shapes.Rectangle(
				box_x, box_y, rp_box_width, rp_box_height, color=RP_GREY,
			)
			label = pyglet.text.Label(
				title, font_name=font_name, font_size=int(height / 70), weight="bold",
				color=WHITE, x=box_x + rp_box_width / 2, y=height * 0.55,
				anchor_x="center", anchor_y="center",
			)
			rp_boxes.append((shape, label, team_key, kind))

	def team_name(team_id):
		for team in (app_state or {}).get("teams", ()):
			if team.eventID == team_id:
				return team.name
		return f"Unknown team {team_id}"

	def update_match_info():
		match = (app_state or {}).get("current_match")
		if match is None:
			match_number_label.text = "Q0"
			red_teams_label.text = "TEAM A\nTEAM B"
			blue_teams_label.text = "TEAM C\nTEAM D"
			return
		match_number_label.text = f"{match.match_type}{match.match_number}"
		red_teams_label.text = f"{team_name(match.red_team_1)}\n{team_name(match.red_team_2)}"
		blue_teams_label.text = f"{team_name(match.blue_team_1)}\n{team_name(match.blue_team_2)}"

	def draw():
		window.clear()
		red_panel.draw()
		blue_panel.draw()
		timer_frame.draw()
		timer_face.draw()
		logo.draw()
		for team_key, label, x in (
			("red", red_label, width * 0.2),
			("blue", blue_label, width * 0.8),
		):
			label.text = str(calc_match_score(state[team_key]))
			label.x = x
			label.y = height * 0.4
			label.draw()

		timer_label.text = timer_text(state, TIMER_SECONDS)
		timer_label.x = width * 0.5
		timer_label.y = height * 0.775
		timer_label.draw()
		update_match_info()
		match_number_label.draw()
		red_teams_label.draw()
		blue_teams_label.draw()
		for shape, label, team_key, kind in rp_boxes:
			scores = state[team_key]
			met = (
				goal_points(scores) >= GOAL_RP_THRESHOLD if kind == "goal"
				else parking_points(scores) >= PARK_RP_THRESHOLD
			)
			shape.color = GOLD if met else RP_GREY
			label.color = (20, 20, 20) if met else WHITE
			shape.draw()
			label.draw()
		if state["timer_state"] == 2:
			for label, team_key, score_key, title in subscore_labels:
				scores = state[team_key]
				if score_key == "foul":
					value = scores["major_foul"] * 15 + scores["minor_foul"] * 5
				else:
					value = scores[score_key]
				label.text = f"{title}: {value}"
				label.draw()

	return draw

