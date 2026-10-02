"""Match/solo timer sound cues: start, warning countdown marks, and end."""
from pathlib import Path

import pyglet

WARNING_TIMESTAMPS = [10, 5]  # seconds remaining at which Warning.mp3 plays

_RESOURCES_DIR = Path(__file__).resolve().parents[1] / "resources"


def _load(filename: str):
	try:
		return pyglet.media.load(str(_RESOURCES_DIR / filename), streaming=False)
	except Exception as error:
		print(f"Could not load sound effect {filename}: {error}")
		return None


_match_start_sound = _load("Match_Start.mp3")
_match_end_sound = _load("Match_End.mp3")
_warning_sound = _load("Warning.mp3")


def _play(sound) -> None:
	if sound is None:
		return
	try:
		sound.play()
	except Exception as error:
		print(f"Could not play sound effect: {error}")


def start_new_timer(state: dict) -> None:
	"""Call when a match/solo timer starts: resets this run's sound tracking and plays the start cue."""
	state["_played_sound_marks"] = set()
	_play(_match_start_sound)


def on_timer_tick(state: dict, remaining: int) -> None:
	"""Call once per frame while the timer is running (timer_state == 1).
	Plays Warning.mp3 once per configured timestamp, and Match_End.mp3 once when it hits zero."""
	played = state.setdefault("_played_sound_marks", set())
	if remaining in WARNING_TIMESTAMPS and remaining not in played:
		played.add(remaining)
		_play(_warning_sound)
	if remaining == 0 and "end" not in played:
		played.add("end")
		_play(_match_end_sound)
