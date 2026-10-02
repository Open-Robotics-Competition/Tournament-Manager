import time
from pathlib import Path

import pyglet
from pyglet import gl

try:
	from . import calculate_rankings
	from .field_display_match import FIELD_WIDTH, FIELD_HEIGHT
except ImportError:
	import calculate_rankings
	from field_display_match import FIELD_WIDTH, FIELD_HEIGHT

WHITE = (255, 255, 255)
GOLD = (255, 204, 0)
PANEL = (38, 43, 50)
ROW_A = (45, 51, 59)
ROW_B = (35, 40, 47)
ROW_RED_WIN = (92, 35, 35)
ROW_BLUE_WIN = (30, 40, 90)
ROW_TIE = (70, 70, 76)
BUTTON = (65, 93, 120)
BUTTON_DISABLED = (55, 58, 62)


def row_color(match, index):
	if not match.played:
		return ROW_A if index % 2 == 0 else ROW_B
	if match.red_score > match.blue_score:
		return ROW_RED_WIN
	if match.blue_score > match.red_score:
		return ROW_BLUE_WIN
	return ROW_TIE


def create_controls(state: dict, font_name: str, window, on_run=None, on_edit=None):
	scale_x = window.width / 900
	panel = pyglet.shapes.RoundedRectangle(
		40 * scale_x, 95, 820 * scale_x, 555, radius=10 * scale_x, color=PANEL
	)
	heading = pyglet.text.Label(
		"MATCH SCHEDULE", font_name=font_name, font_size=32, weight="bold",
		x=450 * scale_x, y=620, anchor_x="center", anchor_y="center", color=WHITE,
	)
	column_heading_match = pyglet.text.Label(
		"MATCH", font_name=font_name, font_size=17, weight="bold",
		x=70 * scale_x, y=572, anchor_x="left", anchor_y="center", color=WHITE,
	)
	column_heading_red = pyglet.text.Label(
		"RED ALLIANCE", font_name=font_name, font_size=17, weight="bold",
		x=145 * scale_x, y=572, anchor_x="left", anchor_y="center", color=WHITE,
	)
	column_heading_blue = pyglet.text.Label(
		"BLUE ALLIANCE", font_name=font_name, font_size=17, weight="bold",
		x=390 * scale_x, y=572, anchor_x="left", anchor_y="center", color=WHITE,
	)
	column_heading_score = pyglet.text.Label(
		"SCORE", font_name=font_name, font_size=17, weight="bold",
		x=645 * scale_x, y=572, anchor_x="center", anchor_y="center", color=WHITE,
	)
	viewport_bottom = 145
	viewport_top = 550
	row_height = 76
	visible_rows = 5
	scroll_offset = 0
	rows = []
	last_schedule_signature = None

	def team_name(team_id, surrogate_ids=()):
		prefix = "*" if team_id in surrogate_ids else ""
		for team in state["teams"]:
			if team.eventID == team_id:
				return f"{prefix}{team.name}"
		return f"{prefix}Unknown team {team_id}"

	def refresh_rows():
		nonlocal rows, last_schedule_signature
		schedule = state["schedule"]
		signature = tuple(
			(
				match.match_number, match.match_type,
				match.red_team_1, match.red_team_2,
				match.blue_team_1, match.blue_team_2,
				match.red_score, match.blue_score, match.played,
				tuple(match.surrogate_team_ids),
			)
			for match in schedule
		)
		if signature == last_schedule_signature:
			return
		last_schedule_signature = signature
		rows = []
		for index, match in enumerate(schedule):
			surrogate_ids = set(match.surrogate_team_ids)
			y = viewport_top - index * row_height - row_height
			background = pyglet.shapes.Rectangle(
				50 * scale_x, y, 800 * scale_x, row_height - 5,
				color=ROW_A if index % 2 == 0 else ROW_B,
			)
			match_number = pyglet.text.Label(
				f"{match.match_type}{match.match_number}", font_name=font_name, font_size=19,
				weight="bold", x=70 * scale_x, y=y + 35,
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			red_names = pyglet.text.Label(
				f"{team_name(match.red_team_1, surrogate_ids)}\n{team_name(match.red_team_2, surrogate_ids)}",
				font_name=font_name, font_size=17, x=145 * scale_x, y=y + 36,
				width=220 * scale_x, multiline=True, align="left",
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			blue_names = pyglet.text.Label(
				f"{team_name(match.blue_team_1, surrogate_ids)}\n{team_name(match.blue_team_2, surrogate_ids)}",
				font_name=font_name, font_size=17, x=390 * scale_x, y=y + 36,
				width=220 * scale_x, multiline=True, align="left",
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			if match.played:
				red_score = max(0, match.red_score)
				blue_score = max(0, match.blue_score)
			else:
				red_score = blue_score = 0
			score = pyglet.text.Label(
				f"{red_score}-{blue_score}",
				font_name=font_name, font_size=20, weight="bold",
				x=645 * scale_x, y=y + 35,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			run_button = pyglet.shapes.RoundedRectangle(
				690 * scale_x, y + 13, 70 * scale_x, 44, radius=5,
				color=BUTTON,
			)
			run_label = pyglet.text.Label(
				"RUN", font_name=font_name, font_size=14, weight="bold",
				x=725 * scale_x, y=y + 35,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			edit_button = pyglet.shapes.RoundedRectangle(
				770 * scale_x, y + 13, 75 * scale_x, 44, radius=5,
				color=BUTTON,
			)
			edit_label = pyglet.text.Label(
				"EDIT", font_name=font_name, font_size=14, weight="bold",
				x=807.5 * scale_x, y=y + 35,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			rows.append((
				match, background, match_number, red_names, blue_names, score,
				run_button, run_label, edit_button, edit_label,
			))

	def draw():
		window.switch_to()
		window.clear()
		panel.draw()
		heading.draw()
		column_heading_match.draw()
		column_heading_red.draw()
		column_heading_blue.draw()
		column_heading_score.draw()
		refresh_rows()
		max_offset = max(0, len(rows) - visible_rows)
		first_row = min(scroll_offset, max_offset)
		vertical_shift = first_row * row_height
		for index, row in enumerate(rows[first_row:first_row + visible_rows], start=first_row):
			match, background, match_number, red_names, blue_names, score, \
				run_button, run_label, edit_button, edit_label = row
			background.color = row_color(match, index)
			edit_button.color = BUTTON if match.played else BUTTON_DISABLED
			for element in (
				background, match_number, red_names, blue_names, score,
				run_button, run_label, edit_button, edit_label,
			):
				element.y += vertical_shift
				element.draw()
				element.y -= vertical_shift

	def handle_click(x, y, button, modifiers):
		if not (viewport_bottom <= y <= viewport_top):
			return False
		max_offset = max(0, len(rows) - visible_rows)
		first_row = min(scroll_offset, max_offset)
		vertical_shift = first_row * row_height
		for row in rows[first_row:first_row + visible_rows]:
			match, _background, _match_number, _red_names, _blue_names, _score, \
				run_button, _run_label, edit_button, _edit_label = row
			if (
				run_button.x <= x <= run_button.x + run_button.width
				and run_button.y + vertical_shift <= y <= run_button.y + vertical_shift + run_button.height
			):
				if on_run is not None:
					on_run(match)
				return True
			if (
				edit_button.x <= x <= edit_button.x + edit_button.width
				and edit_button.y + vertical_shift <= y <= edit_button.y + vertical_shift + edit_button.height
			):
				if match.played and on_edit is not None:
					on_edit(match)
				return True
		return False

	def handle_scroll(x, y, scroll_x, scroll_y):
		nonlocal scroll_offset
		max_offset = max(0, len(state["schedule"]) - visible_rows)
		scroll_offset = min(max(0, scroll_offset - int(scroll_y)), max_offset)
		return True

	return draw, handle_click, handle_scroll


def create_field_renderer(window, state: dict, font_name: str):
	width = window.width
	height = window.height
	scale_x = width / FIELD_WIDTH
	scale_y = height / FIELD_HEIGHT

	background = pyglet.shapes.Rectangle(0, 0, width, height, color=(18, 20, 25))
	divider_x = width * 0.6
	divider = pyglet.shapes.Line(
		divider_x, height * 0.06, divider_x, height * 0.94, thickness=3 * scale_y, color=(70, 74, 80)
	)
	schedule_heading = pyglet.text.Label(
		"MATCH SCHEDULE", font_name=font_name, font_size=int(42 * scale_y), weight="bold",
		x=divider_x / 2, y=height * 0.93, anchor_x="center", anchor_y="center", color=WHITE,
	)
	ranking_heading = pyglet.text.Label(
		"RANKINGS", font_name=font_name, font_size=int(42 * scale_y), weight="bold",
		x=(divider_x + width) / 2, y=height * 0.93, anchor_x="center", anchor_y="center", color=WHITE,
	)
	corner_logo_size = height * 0.1
	corner_logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	corner_logos = []
	for corner_x in (width * 0.02, width - corner_logo_size - width * 0.02):
		corner_logo = pyglet.sprite.Sprite(corner_logo_image)
		corner_logo.scale_x = corner_logo_size / corner_logo_image.width
		corner_logo.scale_y = corner_logo_size / corner_logo_image.height
		corner_logo.x = corner_x
		corner_logo.y = height - corner_logo_size - height * 0.02
		corner_logos.append(corner_logo)

	rank_col_x = divider_x + (width - divider_x) * 0.06
	team_col_x = divider_x + (width - divider_x) * 0.16
	wl_col_x = divider_x + (width - divider_x) * 0.62
	rp_col_x = divider_x + (width - divider_x) * 0.85
	ranking_heading_rank = pyglet.text.Label(
		"RANK", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=rank_col_x, y=height * 0.85, anchor_x="left", anchor_y="center", color=WHITE,
	)
	ranking_heading_team = pyglet.text.Label(
		"TEAM", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=team_col_x, y=height * 0.85, anchor_x="left", anchor_y="center", color=WHITE,
	)
	ranking_heading_wl = pyglet.text.Label(
		"W/L", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=wl_col_x, y=height * 0.85, anchor_x="center", anchor_y="center", color=WHITE,
	)
	ranking_heading_rp = pyglet.text.Label(
		"RP", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=rp_col_x, y=height * 0.85, anchor_x="center", anchor_y="center", color=WHITE,
	)

	ranking_rows = []
	last_ranking_signature = None
	ranking_scroll_pixels = 0.0
	ranking_last_time = None

	column_match_x = width * 0.045
	column_red_x = width * 0.11
	column_blue_x = width * 0.30
	column_score_x = width * 0.48
	column_heading_match = pyglet.text.Label(
		"MATCH", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=column_match_x, y=height * 0.85, anchor_x="left", anchor_y="center", color=WHITE,
	)
	column_heading_red = pyglet.text.Label(
		"RED ALLIANCE", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=column_red_x, y=height * 0.85, anchor_x="left", anchor_y="center", color=WHITE,
	)
	column_heading_blue = pyglet.text.Label(
		"BLUE ALLIANCE", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=column_blue_x, y=height * 0.85, anchor_x="left", anchor_y="center", color=WHITE,
	)
	column_heading_score = pyglet.text.Label(
		"SCORE", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
		x=column_score_x, y=height * 0.85, anchor_x="center", anchor_y="center", color=WHITE,
	)

	viewport_top = height * 0.80
	viewport_bottom = height * 0.08
	visible_row_capacity = 7
	row_height = (viewport_top - viewport_bottom) / visible_row_capacity

	rows = []
	last_schedule_signature = None
	scroll_pixels = 0.0
	last_time = None
	scroll_speed = height * 0.03  # pixels per second

	def team_name(team_id, surrogate_ids=()):
		prefix = "*" if team_id in surrogate_ids else ""
		for team in state["teams"]:
			if team.eventID == team_id:
				return f"{prefix}{team.name}"
		return f"{prefix}Unknown team {team_id}"

	def refresh_rows():
		nonlocal rows, last_schedule_signature
		schedule = state["schedule"]
		signature = tuple(
			(
				match.match_number, match.match_type,
				match.red_team_1, match.red_team_2,
				match.blue_team_1, match.blue_team_2,
				match.red_score, match.blue_score, match.played,
				tuple(match.surrogate_team_ids),
			)
			for match in schedule
		)
		if signature == last_schedule_signature:
			return
		last_schedule_signature = signature
		rows = []
		for index, match in enumerate(schedule):
			surrogate_ids = set(match.surrogate_team_ids)
			row_top = viewport_top - index * row_height
			background_row = pyglet.shapes.Rectangle(
				width * 0.02, row_top - row_height + row_height * 0.08, divider_x - width * 0.04,
				row_height * 0.84, color=ROW_A if index % 2 == 0 else ROW_B,
			)
			match_number = pyglet.text.Label(
				f"{match.match_type}{match.match_number}", font_name=font_name, font_size=int(22 * scale_y),
				weight="bold", x=column_match_x, y=row_top - row_height / 2,
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			red_names = pyglet.text.Label(
				f"{team_name(match.red_team_1, surrogate_ids)}\n{team_name(match.red_team_2, surrogate_ids)}",
				font_name=font_name, font_size=int(18 * scale_y), x=column_red_x,
				y=row_top - row_height / 2, width=column_blue_x - column_red_x - 10 * scale_x,
				multiline=True, align="left", anchor_x="left", anchor_y="center", color=WHITE,
			)
			blue_names = pyglet.text.Label(
				f"{team_name(match.blue_team_1, surrogate_ids)}\n{team_name(match.blue_team_2, surrogate_ids)}",
				font_name=font_name, font_size=int(18 * scale_y), x=column_blue_x,
				y=row_top - row_height / 2, width=column_score_x - column_blue_x - 10 * scale_x,
				multiline=True, align="left", anchor_x="left", anchor_y="center", color=WHITE,
			)
			if match.played:
				red_score = max(0, match.red_score)
				blue_score = max(0, match.blue_score)
			else:
				red_score = blue_score = 0
			score = pyglet.text.Label(
				f"{red_score}-{blue_score}",
				font_name=font_name, font_size=int(24 * scale_y), weight="bold",
				x=column_score_x, y=row_top - row_height / 2,
				anchor_x="center", anchor_y="center", color=WHITE,
			)
			rows.append((row_top, index, match, (background_row, match_number, red_names, blue_names, score)))

	def refresh_rankings():
		nonlocal ranking_rows, last_ranking_signature
		schedule = state["schedule"]
		teams = state["teams"]
		signature = (
			tuple(
				(
					match.red_team_1, match.red_team_2, match.blue_team_1, match.blue_team_2,
					match.red_score, match.blue_score, match.red_rp, match.blue_rp,
					match.played, tuple(match.surrogate_team_ids),
				)
				for match in schedule
			),
			tuple(team.eventID for team in teams),
		)
		if signature == last_ranking_signature:
			return
		last_ranking_signature = signature
		rankings = [
			entry for entry in calculate_rankings.calculate_rankings(schedule, teams)
			if entry["matches_played"] > 0
		]
		ranking_rows = []
		for index, entry in enumerate(rankings):
			row_top = viewport_top - index * row_height
			background_row = pyglet.shapes.Rectangle(
				divider_x + width * 0.02, row_top - row_height + row_height * 0.08,
				width - divider_x - width * 0.04, row_height * 0.84,
				color=ROW_A if index % 2 == 0 else ROW_B,
			)
			rank_label = pyglet.text.Label(
				str(index + 1), font_name=font_name, font_size=int(22 * scale_y), weight="bold",
				x=rank_col_x, y=row_top - row_height / 2, anchor_x="left", anchor_y="center", color=WHITE,
			)
			team_label = pyglet.text.Label(
				entry["team"].name, font_name=font_name, font_size=int(18 * scale_y),
				x=team_col_x, y=row_top - row_height / 2, width=wl_col_x - team_col_x - 10 * scale_x,
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			wl_label = pyglet.text.Label(
				f"{entry['wins']}-{entry['losses']}", font_name=font_name, font_size=int(18 * scale_y),
				x=wl_col_x, y=row_top - row_height / 2, anchor_x="center", anchor_y="center", color=WHITE,
			)
			rp_label = pyglet.text.Label(
				f"{entry['normalized_rp']:.2f}", font_name=font_name, font_size=int(20 * scale_y), weight="bold",
				x=rp_col_x, y=row_top - row_height / 2, anchor_x="center", anchor_y="center", color=GOLD,
			)
			ranking_rows.append((
				row_top, index, (background_row, rank_label, team_label, wl_label, rp_label),
			))

	def draw():
		nonlocal scroll_pixels, last_time, ranking_scroll_pixels, ranking_last_time
		window.switch_to()
		window.clear()
		background.draw()
		divider.draw()
		schedule_heading.draw()
		ranking_heading.draw()
		for corner_logo in corner_logos:
			corner_logo.draw()
		column_heading_match.draw()
		column_heading_red.draw()
		column_heading_blue.draw()
		column_heading_score.draw()
		ranking_heading_rank.draw()
		ranking_heading_team.draw()
		ranking_heading_wl.draw()
		ranking_heading_rp.draw()
		refresh_rows()
		refresh_rankings()

		now = time.time()
		if last_time is None:
			last_time = now
		scroll_should_run = len(rows) > visible_row_capacity
		if scroll_should_run:
			total_height = row_height * len(rows)
			scroll_pixels = (scroll_pixels + scroll_speed * (now - last_time)) % total_height
		else:
			scroll_pixels = 0.0
		last_time = now
		if ranking_last_time is None:
			ranking_last_time = now
		ranking_scroll_should_run = len(ranking_rows) > visible_row_capacity
		if ranking_scroll_should_run:
			ranking_total_height = row_height * len(ranking_rows)
			ranking_scroll_pixels = (
				ranking_scroll_pixels + scroll_speed * (now - ranking_last_time)
			) % ranking_total_height
		else:
			ranking_scroll_pixels = 0.0
		ranking_last_time = now

		if rows:
			total_height = row_height * len(rows)

			# Clip rows at the header boundary so they slide out of view gradually instead of vanishing.
			gl.glEnable(gl.GL_SCISSOR_TEST)
			gl.glScissor(
				int(width * 0.02), 0, int(divider_x - width * 0.04), int(viewport_top)
			)
			for row_top, index, match, elements in rows:
				elements[0].color = row_color(match, index)
				# Draw both the current cycle and the one behind it so a wrap never jumps mid-scroll.
				cycle_offsets = (0.0, total_height) if scroll_should_run else (0.0,)
				for cycle_offset in cycle_offsets:
					offset = scroll_pixels - cycle_offset
					shifted_top = row_top + offset
					if shifted_top < viewport_bottom - row_height or shifted_top > viewport_top + row_height:
						continue
					for element in elements:
						element.y += offset
						element.draw()
						element.y -= offset
			gl.glDisable(gl.GL_SCISSOR_TEST)

		if ranking_rows:
			ranking_total_height = row_height * len(ranking_rows)
			gl.glEnable(gl.GL_SCISSOR_TEST)
			gl.glScissor(
				int(divider_x + width * 0.02), 0, int(width - divider_x - width * 0.04), int(viewport_top)
			)
			for row_top, index, elements in ranking_rows:
				cycle_offsets = (0.0, ranking_total_height) if ranking_scroll_should_run else (0.0,)
				for cycle_offset in cycle_offsets:
					offset = ranking_scroll_pixels - cycle_offset
					shifted_top = row_top + offset
					if shifted_top < viewport_bottom - row_height or shifted_top > viewport_top + row_height:
						continue
					for element in elements:
						element.y += offset
						element.draw()
						element.y -= offset
			gl.glDisable(gl.GL_SCISSOR_TEST)

	return draw
