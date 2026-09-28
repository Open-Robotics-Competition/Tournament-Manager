import math

import pyglet

RED = (166, 25, 25)
GOLD = (255, 204, 0)
WHITE = (255, 255, 255)


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
		count = pyglet.text.Label(
			"0", font_name=font_name, font_size=30 * font_scale, weight="bold",
			x=510 * scale_x, y=y + 29, anchor_x="center", anchor_y="center", color=WHITE,
		)
		drawables.append((label, count, score_key))
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
				label, count, score_key = item
				label.draw()
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

	def handle_click(x, y):
		for shape, _label, value in parking_controls:
			if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
				state["red"]["p1"] = value
				return True
		for shape, _label, callback in reversed(buttons):
			if shape.x <= x <= shape.x + shape.width and shape.y <= y <= shape.y + shape.height:
				callback()
				return True
		return False

	return draw, handle_click
