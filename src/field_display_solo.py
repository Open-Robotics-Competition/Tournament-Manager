from pathlib import Path

import pyglet

try:
	from .scoring_common import calc_solo_score, timer_text
except ImportError:
	from scoring_common import calc_solo_score, timer_text

RED = (166, 25, 25)
GOLD = (255, 190, 0)
WHITE = (255, 255, 255)
FIELD_WIDTH = 1920
FIELD_HEIGHT = 1080
TIMER_SECONDS = 60


def create_renderer(window, state: dict, font_name: str):
	width = window.width
	height = window.height
	scale_x = width / FIELD_WIDTH
	scale_y = height / FIELD_HEIGHT
	border = 15 * min(scale_x, scale_y)
	corner_radius = 30 * min(scale_x, scale_y)
	background = pyglet.shapes.Rectangle(0, 0, width, height, color=RED)

	timer_frame = pyglet.shapes.RoundedRectangle(
		width * 0.075, height * 0.59, width * 0.5, height * 0.34,
		radius=corner_radius, color=GOLD,
	)
	timer_face = pyglet.shapes.RoundedRectangle(
		width * 0.075 + border, height * 0.59 + border,
		width * 0.5 - 2 * border, height * 0.34 - 2 * border,
		radius=corner_radius - border, color=(0, 0, 0),
	)
	logo_path = Path(__file__).resolve().parents[1] / "resources" / "liftoff_logo.png"
	logo_image = pyglet.image.load(str(logo_path))
	logo_size = 900 * scale_y
	logo = pyglet.sprite.Sprite(logo_image)
	logo.scale_x = logo_size / logo_image.width
	logo.scale_y = logo_size / logo_image.height
	logo.x = width * 0.75 - logo_size / 2
	logo.y = (height - logo_size) / 2

	score_font_size = int(height / 4 * 0.75)
	timer_font_size = int(height / 3 * 0.75)
	subscore_font_size = int(height / 16 * 0.75)
	initial_score_height = height * 0.25
	score_box = pyglet.shapes.RoundedRectangle(
		width * 0.075, height * 0.25, width * 0.25, initial_score_height,
		radius=corner_radius, color=GOLD,
	)
	score_face = pyglet.shapes.RoundedRectangle(
		width * 0.075 + border, height * 0.25 + border,
		width * 0.25 - 2 * border, initial_score_height - 2 * border,
		radius=corner_radius - border, color=(0, 0, 0),
	)
	score_label = pyglet.text.Label(
		"0", font_name=font_name, font_size=score_font_size, weight="bold",
		color=WHITE, x=width * 0.2, y=height * 0.385,
		anchor_x="center", anchor_y="center",
	)
	timer_label = pyglet.text.Label(
		"1:00", font_name=font_name, font_size=timer_font_size, weight="bold",
		color=WHITE, x=width * 0.325, y=height * 0.775,
		anchor_x="center", anchor_y="center",
	)
	subscore_labels = []
	for score_key, title, top_fraction in (
		("goal", "GOAL", 0.8),
		("exc", "EXCL", 0.85),
		("p1", "PARK", 0.9),
	):
		label = pyglet.text.Label(
			"", font_name=font_name, font_size=subscore_font_size, weight="bold",
			color=WHITE, x=width * 0.2, y=height * (1 - top_fraction),
			anchor_x="center", anchor_y="center",
		)
		subscore_labels.append((label, score_key, title))

	def draw():
		window.clear()
		background.draw()
		timer_frame.draw()
		timer_face.draw()
		logo.draw()
		box_height = height * (0.45 if state["timer_state"] == 2 else 0.25)
		score_box.height = box_height
		score_box.y = height * (0.5 - box_height / height)
		score_face.y = score_box.y + border
		score_face.height = box_height - 2 * border
		score_box.draw()
		score_face.draw()
		red_scores = state["red"]
		score_label.text = str(calc_solo_score(red_scores))
		score_label.draw()

		timer_label.text = timer_text(state, TIMER_SECONDS)
		timer_label.draw()
		if state["timer_state"] == 2:
			for label, score_key, title in subscore_labels:
				label.text = f"{title}: {red_scores[score_key]}"
				label.draw()

	return draw
