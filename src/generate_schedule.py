from pathlib import Path
import math

import pyglet
from pyglet.window import key

WHITE = (255, 255, 255)
PANEL = (38, 43, 50)
BUTTON = (54, 104, 151)


def create_controls(font_name: str, window, state: dict, on_standard, on_round_robin, on_finalize):
	scale_x = window.width / 900
	font_scale = math.sqrt(scale_x)
	panel = pyglet.shapes.RoundedRectangle(
		40 * scale_x, 125, 820 * scale_x, 525, radius=10 * scale_x, color=PANEL
	)
	heading = pyglet.text.Label(
		"GENERATE QUALIFICATION SCHEDULE",
		font_name=font_name,
		font_size=30 * font_scale,
		weight="bold",
		x=450 * scale_x,
		y=590,
		anchor_x="center",
		anchor_y="center",
		color=WHITE,
	)
	standard_button = pyglet.shapes.RoundedRectangle(
		100 * scale_x, 360, 220 * scale_x, 90, radius=8 * scale_x, color=BUTTON
	)
	standard_label = pyglet.text.Label(
		"STANDARD", font_name=font_name, font_size=24 * font_scale, weight="bold",
		x=210 * scale_x, y=405, anchor_x="center", anchor_y="center", color=WHITE,
	)
	round_robin_button = pyglet.shapes.RoundedRectangle(
		580 * scale_x, 360, 220 * scale_x, 90, radius=8 * scale_x, color=BUTTON
	)
	round_robin_label = pyglet.text.Label(
		"ROUND-ROBIN", font_name=font_name, font_size=24 * font_scale, weight="bold",
		x=690 * scale_x, y=405, anchor_x="center", anchor_y="center", color=WHITE,
	)

	# Batches and iterations entry boxes sit side by side between the standard/round-robin buttons.
	batch_label = pyglet.text.Label(
		"BATCHES", font_name=font_name, font_size=12 * font_scale, weight="bold",
		x=385 * scale_x, y=447, anchor_x="center", anchor_y="center", color=WHITE,
	)
	batch_box = pyglet.shapes.Rectangle(
		350 * scale_x, 405, 70 * scale_x, 34, color=(245, 247, 250)
	)
	batch_value = "1"
	batch_focused = False
	batch_replace_on_type = False
	batch_value_label = pyglet.text.Label(
		batch_value, font_name=font_name, font_size=18 * font_scale,
		x=385 * scale_x, y=422, anchor_x="center", anchor_y="center", color=(20, 24, 30),
	)
	iteration_label = pyglet.text.Label(
		"ITERATIONS", font_name=font_name, font_size=12 * font_scale, weight="bold",
		x=515 * scale_x, y=447, anchor_x="center", anchor_y="center", color=WHITE,
	)
	iteration_box = pyglet.shapes.Rectangle(
		480 * scale_x, 405, 70 * scale_x, 34, color=(245, 247, 250)
	)
	iteration_value = "1"
	iteration_focused = False
	iteration_replace_on_type = False
	iteration_value_label = pyglet.text.Label(
		iteration_value, font_name=font_name, font_size=18 * font_scale,
		x=515 * scale_x, y=422, anchor_x="center", anchor_y="center", color=(20, 24, 30),
	)
	result_status = pyglet.text.Label(
		state["schedule_status"],
		font_name=font_name,
		font_size=11 * font_scale,
		weight="bold",
		x=450 * scale_x,
		y=290,
		width=760 * scale_x,
		multiline=True,
		align="center",
		anchor_x="center",
		anchor_y="center",
		color=WHITE,
	)
	finalize_button = pyglet.shapes.RoundedRectangle(
		365 * scale_x, 150, 270 * scale_x, 58, radius=8 * scale_x, color=(48, 118, 77)
	)
	finalize_label = pyglet.text.Label(
		"FINALIZE SCHEDULE", font_name=font_name, font_size=20 * font_scale, weight="bold",
		x=500 * scale_x, y=179, anchor_x="center", anchor_y="center", color=WHITE,
	)

	def draw():
		window.switch_to()
		panel.draw()
		heading.draw()
		standard_button.draw()
		standard_label.draw()
		batch_label.draw()
		batch_box.color = (255, 204, 0) if batch_focused else (245, 247, 250)
		batch_box.draw()
		batch_value_label.text = batch_value
		batch_value_label.draw()
		iteration_label.draw()
		iteration_box.color = (255, 204, 0) if iteration_focused else (245, 247, 250)
		iteration_box.draw()
		iteration_value_label.text = iteration_value
		iteration_value_label.draw()
		round_robin_button.draw()
		round_robin_label.draw()
		result_status.text = state["schedule_status"]
		result_status.draw()
		schedule_ready = bool(state["schedule"])
		finalize_button.color = (48, 118, 77) if schedule_ready else (70, 74, 80)
		finalize_button.draw()
		finalize_label.color = WHITE if schedule_ready else (140, 143, 148)
		finalize_label.draw()

	def handle_click(x, y):
		nonlocal batch_focused, batch_replace_on_type, iteration_focused, iteration_replace_on_type
		if (
			batch_box.x <= x <= batch_box.x + batch_box.width
			and batch_box.y <= y <= batch_box.y + batch_box.height
		):
			batch_focused = True
			batch_replace_on_type = True
			iteration_focused = False
			iteration_replace_on_type = False
			return True
		if (
			iteration_box.x <= x <= iteration_box.x + iteration_box.width
			and iteration_box.y <= y <= iteration_box.y + iteration_box.height
		):
			iteration_focused = True
			iteration_replace_on_type = True
			batch_focused = False
			batch_replace_on_type = False
			return True
		batch_focused = False
		batch_replace_on_type = False
		iteration_focused = False
		iteration_replace_on_type = False
		if (
			standard_button.x <= x <= standard_button.x + standard_button.width
			and standard_button.y <= y <= standard_button.y + standard_button.height
		):
			try:
				batch_count = int(batch_value)
				iteration_count = int(iteration_value)
			except ValueError:
				state["schedule_status"] = "ENTER A VALID BATCH/ITERATION COUNT"
				return True
			on_standard(batch_count, iteration_count)
			return True
		if (
			round_robin_button.x <= x <= round_robin_button.x + round_robin_button.width
			and round_robin_button.y <= y <= round_robin_button.y + round_robin_button.height
		):
			try:
				batch_count = int(batch_value)
				iteration_count = int(iteration_value)
			except ValueError:
				state["schedule_status"] = "ENTER A VALID BATCH/ITERATION COUNT"
				return True
			on_round_robin(batch_count, iteration_count)
			return True
		if (
			finalize_button.x <= x <= finalize_button.x + finalize_button.width
			and finalize_button.y <= y <= finalize_button.y + finalize_button.height
		):
			if state["schedule"]:
				on_finalize()
			return True
		return False

	def handle_text(text):
		nonlocal batch_value, batch_replace_on_type, iteration_value, iteration_replace_on_type
		if batch_focused:
			if text.isdigit():
				if batch_replace_on_type:
					batch_value = text
					batch_replace_on_type = False
				else:
					batch_value += text
		elif iteration_focused:
			if text.isdigit():
				if iteration_replace_on_type:
					iteration_value = text
					iteration_replace_on_type = False
				else:
					iteration_value += text

	def handle_text_motion(motion):
		nonlocal batch_value, batch_replace_on_type, iteration_value, iteration_replace_on_type
		if batch_focused and motion == key.MOTION_BACKSPACE:
			if batch_replace_on_type:
				batch_value = ""
				batch_replace_on_type = False
			else:
				batch_value = batch_value[:-1]
		elif iteration_focused and motion == key.MOTION_BACKSPACE:
			if iteration_replace_on_type:
				iteration_value = ""
				iteration_replace_on_type = False
			else:
				iteration_value = iteration_value[:-1]

	def handle_key_press(symbol, modifiers):
		nonlocal batch_value, batch_focused, batch_replace_on_type
		nonlocal iteration_value, iteration_focused, iteration_replace_on_type
		if batch_focused and symbol == key.ENTER:
			batch_focused = False
		elif batch_focused and symbol == key.A and modifiers & key.MOD_CTRL:
			batch_value = ""
			batch_replace_on_type = False
		elif iteration_focused and symbol == key.ENTER:
			iteration_focused = False
		elif iteration_focused and symbol == key.A and modifiers & key.MOD_CTRL:
			iteration_value = ""
			iteration_replace_on_type = False

	return draw, handle_click, handle_text, handle_text_motion, handle_key_press


def create_field_renderer(window, font_name: str):
	width = window.width
	height = window.height
	background = pyglet.shapes.Rectangle(0, 0, width, height, color=(18, 20, 25))
	logo_path = Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"
	logo_image = pyglet.image.load(str(logo_path))
	logo_size = min(height * 0.58, width * 0.58)
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = (width - logo_size) / 2
	logo.y = height * 0.3
	status = pyglet.text.Label(
		"GENERATING QUALIFICATION SCHEDULE",
		font_name=font_name,
		font_size=58,
		weight="bold",
		x=width / 2,
		y=height * 0.13,
		width=width - 160,
		multiline=True,
		align="center",
		anchor_x="center",
		anchor_y="center",
		color=WHITE,
	)

	def draw():
		window.switch_to()
		window.clear()
		background.draw()
		logo.draw()
		status.draw()

	return draw
