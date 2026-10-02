import math

import pyglet
from pyglet.window import key

try:
	from . import scoring_common
except ImportError:
	import scoring_common


RED = (166, 25, 25)
BLUE = (26, 30, 171)
GOLD = (255, 204, 0)
WHITE = (255, 255, 255)
RP_GREY = (90, 93, 98)
ENTRY_BOX_COLOR = (245, 247, 250)
ENTRY_BOX_FOCUS_COLOR = (255, 204, 0)
ENTRY_TEXT_COLOR = (20, 24, 30)


def create_controls(window, state: dict, font_name: str):
	scale_x = window.width / 900
	font_scale = math.sqrt(scale_x)
	buttons = []
	parking_controls = []
	parking_labels = []
	value_labels = []
	score_rp_labels = []
	rp_boxes = []
	entry_boxes = []

	for team_name, team_key, team_color, column_x in (
		("RED", "red", RED, 20 * scale_x),
		("BLUE", "blue", BLUE, 460 * scale_x),
	):
		panel = pyglet.shapes.RoundedRectangle(
			column_x, 170, 420 * scale_x, 500, radius=12 * scale_x,
			color=tuple(int(channel * 0.45) for channel in team_color),
		)
		team_heading = pyglet.text.Label(
			team_name, font_name=font_name, font_size=36 * font_scale, weight="bold",
			x=column_x + 190 * scale_x, y=625, anchor_x="center", anchor_y="center",
			color=WHITE,
		)
		value_labels.append((panel, team_heading))

		opponent_key = "blue" if team_key == "red" else "red"
		score_rp_label = pyglet.text.Label(
			"SCORE 0   RP 0", font_name=font_name, font_size=15 * font_scale, weight="bold",
			x=column_x + 16 * scale_x, y=625, anchor_x="left", anchor_y="center", color=WHITE,
		)
		score_rp_labels.append((score_rp_label, team_key, opponent_key))
		for index, (kind, title) in enumerate((("goal", "GOAL RP"), ("park", "PARK RP"))):
			box_x = column_x + (250 + index * 80) * scale_x
			shape = pyglet.shapes.RoundedRectangle(
				box_x, 612, 75 * scale_x, 26, radius=4 * scale_x, color=RP_GREY,
			)
			label = pyglet.text.Label(
				title, font_name=font_name, font_size=11 * font_scale, weight="bold",
				x=box_x + 37.5 * scale_x, y=625, anchor_x="center", anchor_y="center", color=WHITE,
			)
			rp_boxes.append((shape, label, team_key, kind))
		for score_key, title, y in (
			("goal", "GOALS", 535),
			("exc", "EXCLUSION ZONE", 465),
			("p1", "PARK1", 395),
			("p2", "PARK 2", 325),
			("major_foul", "MAJOR FOULS", 255),
			("minor_foul", "MINOR FOULS", 185),
		):
			name_label = pyglet.text.Label(
				title, font_name=font_name,
				font_size=(16 if score_key in ("p1", "p2") else 18) * font_scale,
				weight="bold",
				x=column_x + 16 * scale_x, y=y + 26,
				anchor_x="left", anchor_y="center", color=WHITE,
			)
			if score_key in ("p1", "p2"):
				name_label.x = column_x + 12 * scale_x
				parking_labels.append(name_label)
				for option, text, option_width, offset in (
					(0, "NONE", 82, 130),
					(1, "PARTIAL", 104, 216),
					(2, "FULL", 82, 324),
				):
					x = column_x + offset * scale_x
					option_width *= scale_x
					shape = pyglet.shapes.RoundedRectangle(
						x, y, option_width, 52, radius=6 * scale_x,
						color=tuple(min(255, c + 28) for c in team_color),
					)
					label = pyglet.text.Label(
						text, font_name=font_name, font_size=14 * font_scale, weight="bold",
						x=x + option_width / 2, y=y + 26,
						anchor_x="center", anchor_y="center", color=WHITE,
					)
					parking_controls.append((shape, label, team_key, score_key, option))
				continue

			count_label = pyglet.text.Label(
				"0", font_name=font_name, font_size=22 * font_scale, weight="bold",
				x=column_x + 260 * scale_x, y=y + 26,
				anchor_x="center", anchor_y="center",
				color=ENTRY_TEXT_COLOR if score_key in ("goal", "exc") else WHITE,
			)
			if score_key in ("goal", "exc"):
				entry_box = pyglet.shapes.Rectangle(
					column_x + 225 * scale_x, y, 70 * scale_x, 52, color=ENTRY_BOX_COLOR,
				)
				entry_boxes.append({
					"shape": entry_box, "label": count_label, "team_key": team_key, "score_key": score_key,
					"buffer": str(state[team_key][score_key]), "focused": False, "replace_on_type": False,
				})
				value_labels.append((name_label,))
			else:
				value_labels.append((name_label, count_label, team_key, score_key))
			for button_x, text, delta in (
				(column_x + 300 * scale_x, "-", -1),
				(column_x + 360 * scale_x, "+", 1),
			):
				def adjust(team=team_key, item=score_key, change=delta):
					new_value = state[team][item] + change
					if new_value >= 0:
						state[team][item] = new_value

				shape = pyglet.shapes.RoundedRectangle(
					button_x, y, 52 * scale_x, 52, radius=8 * scale_x,
					color=tuple(min(255, c + 28) for c in team_color),
				)
				label = pyglet.text.Label(
					text, font_name=font_name, font_size=22 * font_scale, weight="bold",
					x=button_x + 26 * scale_x, y=y + 26,
					anchor_x="center", anchor_y="center", color=WHITE,
				)
				buttons.append((shape, label, adjust))

	def draw():
		for item in value_labels:
			if len(item) == 2:
				for drawable in item:
					drawable.draw()
			elif len(item) == 1:
				item[0].draw()
			else:
				name_label, count_label, team_key, score_key = item
				name_label.draw()
				count_label.text = str(state[team_key][score_key])
				count_label.draw()
		for label in parking_labels:
			label.draw()
		for shape, label, team_key, score_key, option in parking_controls:
			shape.color = (
				GOLD if state[team_key][score_key] == option
				else tuple(min(255, c + 28) for c in (RED if team_key == "red" else BLUE))
			)
			shape.draw()
			label.draw()
		for shape, label, _callback in buttons:
			shape.draw()
			label.draw()
		for label, team_key, opponent_key in score_rp_labels:
			own_scores = state[team_key]
			opponent_scores = state[opponent_key]
			own_total = scoring_common.calc_match_score(own_scores)
			opponent_total = scoring_common.calc_match_score(opponent_scores)
			rp = scoring_common.calc_match_rp(own_scores, own_total, opponent_total)
			label.text = f"SCORE {own_total}   RP {rp}"
			label.draw()
		for shape, label, team_key, kind in rp_boxes:
			scores = state[team_key]
			met = (
				scoring_common.goal_points(scores) >= scoring_common.GOAL_RP_THRESHOLD if kind == "goal"
				else scoring_common.parking_points(scores) >= scoring_common.PARK_RP_THRESHOLD
			)
			shape.color = GOLD if met else RP_GREY
			label.color = (20, 20, 20) if met else WHITE
			shape.draw()
			label.draw()
		for entry in entry_boxes:
			if not entry["focused"]:
				entry["buffer"] = str(state[entry["team_key"]][entry["score_key"]])
			entry["shape"].color = ENTRY_BOX_FOCUS_COLOR if entry["focused"] else ENTRY_BOX_COLOR
			entry["shape"].draw()
			entry["label"].text = entry["buffer"]
			entry["label"].draw()

	def handle_click(x, y):
		for entry in entry_boxes:
			shape = entry["shape"]
			is_hit = shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height
			entry["focused"] = is_hit
			entry["replace_on_type"] = is_hit
		if any(entry["focused"] for entry in entry_boxes):
			return True
		for shape, _label, team_key, score_key, option in parking_controls:
			if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
				state[team_key][score_key] = option
				return True
		for shape, _label, callback in reversed(buttons):
			if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
				callback()
				return True
		return False

	def _focused_entry():
		for entry in entry_boxes:
			if entry["focused"]:
				return entry
		return None

	def handle_text(text):
		entry = _focused_entry()
		if entry is None or not text.isdigit():
			return
		if entry["replace_on_type"]:
			entry["buffer"] = text
			entry["replace_on_type"] = False
		else:
			entry["buffer"] += text
		if entry["buffer"]:
			state[entry["team_key"]][entry["score_key"]] = int(entry["buffer"])

	def handle_text_motion(motion):
		entry = _focused_entry()
		if entry is None or motion != key.MOTION_BACKSPACE:
			return
		if entry["replace_on_type"]:
			entry["buffer"] = ""
			entry["replace_on_type"] = False
		else:
			entry["buffer"] = entry["buffer"][:-1]
		if entry["buffer"]:
			state[entry["team_key"]][entry["score_key"]] = int(entry["buffer"])

	def handle_key_press(symbol, modifiers):
		entry = _focused_entry()
		if entry is None:
			return
		if symbol == key.ENTER:
			entry["focused"] = False
			if not entry["buffer"]:
				entry["buffer"] = str(state[entry["team_key"]][entry["score_key"]])
		elif symbol == key.A and modifiers & key.MOD_CTRL:
			entry["buffer"] = ""
			entry["replace_on_type"] = False

	return draw, handle_click, handle_text, handle_text_motion, handle_key_press
