import csv
import math
from pathlib import Path

import pyglet
from pyglet.window import key

try:
	from . import schedule_io
	from .Team import Team
except ImportError:
	import schedule_io
	from Team import Team

WHITE = (255, 255, 255)
PANEL = (38, 43, 50)
BUTTON = (48, 118, 77)
RESUME_COLOR = (54, 104, 151)
RESUME_DISABLED_COLOR = (60, 63, 68)
tournament_data_path = str(Path(__file__).resolve().parents[1] / "tournament_data")


def read_team_list(tournament_data_path: str) -> list[Team]:
	input_path = Path(tournament_data_path) / "team_list.txt"
	teams = []
	with input_path.open("r", newline="", encoding="utf-8") as team_file:
		reader = csv.DictReader(team_file)
		for row in reader:
			team = Team()
			team.eventID = int(row["eventID"])
			team.name = row["name"]
			team.bestSoloScore = int(row["bestSoloScore"]) if row.get("bestSoloScore") else 0
			teams.append(team)
	return teams


def _validate_tournament_data() -> bool:
	team_list_path = Path(tournament_data_path) / "team_list.txt"
	schedule_path = Path(tournament_data_path) / "schedule.txt"
	if not team_list_path.exists() or not schedule_path.exists():
		return False
	try:
		teams = read_team_list(tournament_data_path)
		schedule = schedule_io.read_schedule(tournament_data_path)
	except (OSError, ValueError, KeyError):
		return False
	return bool(teams) and bool(schedule)


def create_controls(state: dict, font_name: str, window):
	window.switch_to()
	scale_x = window.width / 900
	font_scale = math.sqrt(scale_x)
	input_text = ""
	cursor_position = 0
	input_focused = False
	input_box = pyglet.shapes.Rectangle(70 * scale_x, 125, 760 * scale_x, 390, color=(16, 19, 24))
	input_border = pyglet.shapes.Rectangle(68 * scale_x, 123, 764 * scale_x, 394, color=(190, 196, 204))
	input_label = pyglet.text.Label(
		"", font_name=font_name, font_size=22 * font_scale,
		x=86 * scale_x, y=503, width=728 * scale_x, height=366,
		multiline=True, align="left", anchor_x="left", anchor_y="top",
		color=(245, 247, 250, 255),
	)
	panel = pyglet.shapes.RoundedRectangle(
		40 * scale_x, 105, 820 * scale_x, 560, radius=10 * scale_x, color=PANEL
	)
	title = pyglet.text.Label(
		"TOURNAMENT SETUP", font_name=font_name, font_size=34, weight="bold",
		x=70 * scale_x, y=625, anchor_x="left", anchor_y="center", color=WHITE,
	)
	field_label = pyglet.text.Label(
		"TEAM NAMES", font_name=font_name, font_size=18, weight="bold",
		x=70 * scale_x, y=575, anchor_x="left", anchor_y="center", color=WHITE,
	)
	instruction = pyglet.text.Label(
		"Separate names with commas", font_name=font_name, font_size=16,
		x=70 * scale_x, y=540, anchor_x="left", anchor_y="center", color=(185, 192, 202, 255),
	)
	update_shape = pyglet.shapes.RoundedRectangle(53 * scale_x, 8, 210 * scale_x, 58, radius=8 * scale_x, color=BUTTON)
	update_label = pyglet.text.Label(
		"UPDATE TEAM LIST", font_name=font_name, font_size=15 * font_scale, weight="bold",
		x=158 * scale_x, y=37, anchor_x="center", anchor_y="center", color=WHITE,
	)
	paste_shape = pyglet.shapes.RoundedRectangle(271 * scale_x, 8, 190 * scale_x, 58, radius=8 * scale_x, color=(73, 111, 72))
	paste_label = pyglet.text.Label(
		"PASTE TEAM LIST", font_name=font_name, font_size=15 * font_scale, weight="bold",
		x=366 * scale_x, y=37, anchor_x="center", anchor_y="center", color=WHITE,
	)
	finalize_shape = pyglet.shapes.RoundedRectangle(469 * scale_x, 8, 235 * scale_x, 58, radius=8 * scale_x, color=(54, 104, 151))
	finalize_label = pyglet.text.Label(
		"FINALIZE TEAM LIST", font_name=font_name, font_size=17 * font_scale, weight="bold",
		x=586 * scale_x, y=37, anchor_x="center", anchor_y="center", color=WHITE,
	)
	resume_enabled = _validate_tournament_data()
	resume_shape = pyglet.shapes.RoundedRectangle(
		712 * scale_x, 8, 135 * scale_x, 58, radius=8 * scale_x,
		color=RESUME_COLOR if resume_enabled else RESUME_DISABLED_COLOR,
	)
	resume_label = pyglet.text.Label(
		"RESUME\nTOURNAMENT", font_name=font_name, font_size=12 * font_scale, weight="bold",
		x=779 * scale_x, y=37, width=135 * scale_x, multiline=True, align="center",
		anchor_x="center", anchor_y="center", color=WHITE,
	)
	status = pyglet.text.Label(
		"No teams loaded", font_name=font_name, font_size=18 * font_scale,
		x=70 * scale_x, y=96, anchor_x="left", anchor_y="center", color=WHITE,
	)
	logo_size = 64 * scale_x
	logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = (40 + 820) * scale_x - logo_size - 10 * scale_x
	logo.y = 665 - logo_size - 8

	def update_team_list():
		team_names = [name.strip() for name in input_text.split(",") if name.strip()]
		teams = []
		seen_names = set()
		duplicates_removed = 0
		for name in team_names:
			normalized_name = name.casefold()
			if normalized_name in seen_names:
				duplicates_removed += 1
				continue
			seen_names.add(normalized_name)
			team = Team()
			team.name = name
			team.eventID = len(teams)
			teams.append(team)
		state["teams"] = teams
		state["team_list_revision"] += 1
		status.text = f"{len(teams)} team{'s' if len(teams) != 1 else ''} loaded"
		if duplicates_removed:
			status.text += f"; removed {duplicates_removed} duplicate{'s' if duplicates_removed != 1 else ''}"

	def finalize_team_list():
		update_team_list()
		output_path = Path(tournament_data_path) / "team_list.txt"
		try:
			output_path.parent.mkdir(parents=True, exist_ok=True)
			with output_path.open("w", newline="", encoding="utf-8") as team_file:
				writer = csv.writer(team_file)
				writer.writerow(("eventID", "name", "bestSoloScore"))
				for team in state["teams"]:
					writer.writerow((team.eventID, team.name, team.bestSoloScore))
			status.text = f"Finalized {len(state['teams'])} teams"
		except OSError as error:
			status.text = f"Could not save team list: {error}"

	def resume_tournament():
		if not resume_enabled:
			return
		try:
			teams = read_team_list(tournament_data_path)
			schedule = schedule_io.read_schedule(tournament_data_path)
		except (OSError, ValueError, KeyError) as error:
			status.text = f"Could not resume tournament: {error}"
			return
		state["teams"] = teams
		state["team_list_revision"] += 1
		state["schedule"] = schedule
		state["schedule_finalized"] = True
		state["active_mode"] = "MATCH SCHEDULE"
		status.text = f"Resumed tournament with {len(teams)} teams and {len(schedule)} matches"

	def draw():
		window.switch_to()
		panel.draw()
		title.draw()
		field_label.draw()
		instruction.draw()
		logo.draw()
		input_border.color = (255, 204, 0) if input_focused else (190, 196, 204)
		input_border.draw()
		input_box.draw()
		input_label.text = (
			input_text[:cursor_position] + ("|" if input_focused else "") + input_text[cursor_position:]
		)
		input_box.height = min(400, max(390, input_label.content_height + 24))
		input_border.height = input_box.height + 4
		input_border.y = input_box.y - 2
		input_label.y = input_box.y + input_box.height - 12
		input_label.height = input_box.height - 24
		input_label.draw()
		update_shape.draw()
		update_label.draw()
		paste_shape.draw()
		paste_label.draw()
		finalize_shape.draw()
		finalize_label.draw()
		resume_shape.draw()
		resume_label.draw()
		status.draw()

	def handle_click(x, y, buttons, modifiers):
		nonlocal input_text, input_focused, cursor_position
		if update_shape.x <= x <= update_shape.x + update_shape.width and update_shape.y <= y <= update_shape.y + update_shape.height:
			input_focused = False
			update_team_list()
			return True
		if paste_shape.x <= x <= paste_shape.x + paste_shape.width and paste_shape.y <= y <= paste_shape.y + paste_shape.height:
			pasted_text = window.get_clipboard_text()
			pasted_text = pasted_text.replace("\r\n", "\n").replace("\r", "\n")
			pasted_text = pasted_text.replace("\n", ", ").replace("\t", ", ").strip()
			if pasted_text:
				separator = ", " if input_text and not input_text.rstrip().endswith(",") else ""
				input_text += separator + pasted_text
				cursor_position = len(input_text)
			input_focused = False
			return True
		if finalize_shape.x <= x <= finalize_shape.x + finalize_shape.width and finalize_shape.y <= y <= finalize_shape.y + finalize_shape.height:
			input_focused = False
			finalize_team_list()
			return True
		if (
			resume_enabled
			and resume_shape.x <= x <= resume_shape.x + resume_shape.width
			and resume_shape.y <= y <= resume_shape.y + resume_shape.height
		):
			input_focused = False
			resume_tournament()
			return True
		inside_input = input_box.x <= x <= input_box.x + input_box.width and input_box.y <= y <= input_box.y + input_box.height
		input_focused = inside_input
		if inside_input:
			cursor_position = len(input_text)
		return inside_input

	def handle_text(text):
		nonlocal input_text, cursor_position
		if not input_focused:
			return
		if text in ("\r", "\n"):
			update_team_list()
			return
		input_text = input_text[:cursor_position] + text + input_text[cursor_position:]
		cursor_position += len(text)

	def handle_text_motion(motion):
		nonlocal input_text, cursor_position
		if not input_focused:
			return
		if motion == key.MOTION_LEFT:
			cursor_position = max(0, cursor_position - 1)
		elif motion == key.MOTION_RIGHT:
			cursor_position = min(len(input_text), cursor_position + 1)
		elif motion == key.MOTION_BACKSPACE and cursor_position > 0:
			input_text = input_text[:cursor_position - 1] + input_text[cursor_position:]
			cursor_position -= 1
		elif motion == key.MOTION_DELETE and cursor_position < len(input_text):
			input_text = input_text[:cursor_position] + input_text[cursor_position + 1:]

	def handle_key_press(symbol, modifiers):
		nonlocal input_text, cursor_position
		if not input_focused:
			return
		if symbol == key.ENTER:
			update_team_list()
		elif symbol == key.HOME:
			cursor_position = 0
		elif symbol == key.END:
			cursor_position = len(input_text)
		elif symbol == key.A and modifiers & key.MOD_CTRL:
			input_text = ""
			cursor_position = 0

	return draw, handle_click, handle_text, handle_text_motion, handle_key_press




def create_field_renderer(window, state: dict, font_name: str):
	background = pyglet.shapes.Rectangle(
		0, 0, window.width, window.height, color=(18, 20, 25)
	)
	heading = pyglet.text.Label(
		"TOURNAMENT TEAMS", font_name=font_name, font_size=72, weight="bold",
		x=window.width / 2, y=window.height - 100,
		anchor_x="center", anchor_y="center", color=WHITE,
	)
	empty_message = pyglet.text.Label(
		"No teams entered", font_name=font_name, font_size=42,
		x=window.width / 2, y=window.height / 2,
		anchor_x="center", anchor_y="center", color=WHITE,
	)
	logo_size = window.height * 0.16
	logo_image = pyglet.image.load(str(Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"))
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = window.width - logo_size - window.width * 0.02
	logo.y = window.height - logo_size - window.height * 0.02
	labels = []
	last_revision = -1

	def refresh_labels():
		nonlocal last_revision, labels
		if state["team_list_revision"] == last_revision:
			return
		last_revision = state["team_list_revision"]
		team_count = len(state["teams"])
		columns = max(1, math.ceil(team_count / 16))
		rows = max(1, math.ceil(team_count / columns))
		row_height = min(58, (window.height - 220) / rows)
		column_width = window.width / columns
		font_size = max(18, min(52, int(row_height * 0.8), int(column_width / 8)))
		labels = []
		for index, team in enumerate(state["teams"]):
			column = index // rows
			row = index % rows
			labels.append(pyglet.text.Label(
				team.name, font_name=font_name, font_size=font_size, weight="bold",
				x=column * column_width + 50,
				y=window.height - 190 - row * row_height,
				width=max(40, column_width - 80), height=row_height,
				multiline=True, align="left",
				anchor_x="left", anchor_y="center", color=WHITE,
			))

	def draw():
		window.clear()
		background.draw()
		heading.draw()
		logo.draw()
		refresh_labels()
		if not labels:
			empty_message.draw()
		for label in labels:
			label.draw()

	return draw
