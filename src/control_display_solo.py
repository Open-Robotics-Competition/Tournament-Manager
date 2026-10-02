import math

import pyglet
from pyglet.window import key

RED = (166, 25, 25)
GOLD = (255, 204, 0)
WHITE = (255, 255, 255)
ENTRY_BOX_COLOR = (245, 247, 250)
ENTRY_BOX_FOCUS_COLOR = (255, 204, 0)
ENTRY_TEXT_COLOR = (20, 24, 30)


def create_controls(state: dict, font_name: str, window):
	scale_x = window.width / 900
	font_scale = math.sqrt(scale_x)
	red = pyglet.shapes.RoundedRectangle(
		20 * scale_x, 145, 860 * scale_x, 525, radius=12 * scale_x,
		color=tuple(int(c * 0.45) for c in RED)
	)
	heading = pyglet.text.Label(
		"RED", font_name=font_name, font_size=36 * font_scale, weight="bold",
		x=450 * scale_x, y=625, anchor_x="center", anchor_y="center", color=WHITE,
	)
	drawables = [red, heading]
	buttons = []
	parking_controls = []
	entry_boxes = []

	def add_button(x, y, width, text, callback, color):
		shape = pyglet.shapes.RoundedRectangle(
			x * scale_x, y, width * scale_x, 58, radius=8 * scale_x, color=color
		)
		label = pyglet.text.Label(
			text, font_name=font_name, font_size=22 * font_scale, weight="bold",
			x=(x + width / 2) * scale_x, y=y + 29,
			anchor_x="center", anchor_y="center", color=WHITE,
		)
		buttons.append((shape, label, callback))

	for score_key, title, y in (
		("goal", "GOALS", 510),
		("exc", "EXCLUSION ZONE", 425),
		("major_foul", "MAJOR FOULS", 245),
		("minor_foul", "MINOR FOULS", 165),
	):
		label = pyglet.text.Label(
			title, font_name=font_name, font_size=26 * font_scale, weight="bold",
			x=170 * scale_x, y=y + 29, anchor_x="left", anchor_y="center", color=WHITE,
		)
		drawables.append(label)
		if score_key in ("goal", "exc"):
			count = pyglet.text.Label(
				str(state["red"][score_key]), font_name=font_name, font_size=30 * font_scale, weight="bold",
				x=510 * scale_x, y=y + 29, anchor_x="center", anchor_y="center", color=ENTRY_TEXT_COLOR,
			)
			entry_box = pyglet.shapes.Rectangle(
				465 * scale_x, y, 90 * scale_x, 58, color=ENTRY_BOX_COLOR,
			)
			entry_boxes.append({
				"shape": entry_box, "label": count, "score_key": score_key,
				"buffer": str(state["red"][score_key]), "focused": False, "replace_on_type": False,
			})
		else:
			count = pyglet.text.Label(
				"0", font_name=font_name, font_size=30 * font_scale, weight="bold",
				x=510 * scale_x, y=y + 29, anchor_x="center", anchor_y="center", color=WHITE,
			)
			drawables.append((count, score_key))
		for x, text, delta in ((610, "-", -1), (740, "+", 1)):
			def adjust(item=score_key, change=delta):
				state["red"][item] = max(0, state["red"][item] + change)

			add_button(x, y, 64, text, adjust, tuple(min(255, c + 28) for c in RED))

	park_label = pyglet.text.Label(
		"PARK", font_name=font_name, font_size=26 * font_scale, weight="bold",
		x=170 * scale_x, y=354, anchor_x="left", anchor_y="center", color=WHITE,
	)
	drawables.append(park_label)
	for value, text, x, width in (
		(0, "NONE", 350, 130),
		(1, "PARTIAL", 495, 160),
		(2, "FULL", 670, 130),
	):
		shape = pyglet.shapes.RoundedRectangle(
			x * scale_x, 325, width * scale_x, 58, radius=8 * scale_x,
			color=tuple(min(255, c + 28) for c in RED),
		)
		label = pyglet.text.Label(
			text, font_name=font_name, font_size=18 * font_scale, weight="bold",
			x=(x + width / 2) * scale_x, y=354, anchor_x="center", anchor_y="center", color=WHITE,
		)
		parking_controls.append((shape, label, value))

	def draw():
		for item in drawables:
			if isinstance(item, tuple):
				count, score_key = item
				count.text = str(state["red"][score_key])
				count.draw()
			else:
				item.draw()
		for shape, label, value in parking_controls:
			shape.color = GOLD if state["red"]["p1"] == value else tuple(min(255, c + 28) for c in RED)
			shape.draw()
			label.draw()
		for shape, label, _callback in buttons:
			shape.draw()
			label.draw()
		for entry in entry_boxes:
			if not entry["focused"]:
				entry["buffer"] = str(state["red"][entry["score_key"]])
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
		for shape, _label, value in parking_controls:
			if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
				state["red"]["p1"] = value
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
			state["red"][entry["score_key"]] = int(entry["buffer"])

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
			state["red"][entry["score_key"]] = int(entry["buffer"])

	def handle_key_press(symbol, modifiers):
		entry = _focused_entry()
		if entry is None:
			return
		if symbol == key.ENTER:
			entry["focused"] = False
			if not entry["buffer"]:
				entry["buffer"] = str(state["red"][entry["score_key"]])
		elif symbol == key.A and modifiers & key.MOD_CTRL:
			entry["buffer"] = ""
			entry["replace_on_type"] = False

	return draw, handle_click, handle_text, handle_text_motion, handle_key_press
